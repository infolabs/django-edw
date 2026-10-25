# -*- coding: utf-8 -*-
"""
E7/E9/E11: scoped, whole-batch admission for bulk POST/upsert on the real
InfLabs bulk API.

``djangorestframework-bulk`` 0.3.x calls
``BulkListSerializer.validate_bulk_create(validated_data)`` once for the whole
batch, before the first write, and refuses lookup-retaining POST unless the
consumer supplies an explicit policy.  Its default implementation is empty on
purpose (see the provider docstring: "Lookup retention does not authorize a
global child.create() upsert").

EDW implements that policy here:

* identity is resolved only inside the queryset of the concrete DRF view
  (``view.get_queryset()`` + ``view.filter_queryset()``), not through the global
  model manager;
* the whole batch is admitted before any object is written;
* existing targets are authorized with the view's per-object permission check;
* duplicate or ambiguous identities, and new objects without the declared
  natural key, fail the complete batch;
* a new natural key may not silently shadow an object that exists outside the
  permitted scope;
* only one write database alias is used for lookups and writes.  This is a
  single-database transaction; no distributed atomicity is claimed.

E11/R3 makes the admission *two-stage and whole-batch*:

1. **admission pass** -- for every item in the batch, only the typed identity
   fields are converted (``Field.to_internal_value``; the child serializer's
   field hooks are not run), the scoped target is resolved, the per-object
   permission is decided and duplicates/unknown/out-of-scope identities are
   refused.  A batch that fails here never reaches a state-aware validator and
   never writes;
2. **validation pass** -- every admitted item is validated with
   ``child.instance`` bound to the admitted target (``None`` for a create), so
   real Dynamic RESTMeta ``create``/``update``/``validate`` hooks see the right
   state.  Afterwards the validated identity must still be exactly the admitted
   identity (a hook that re-points ``id``/``slug`` is refused, never resolved
   again), and the admitted target is re-checked immediately before the write.

The plan built in stage 1 is the only authority for ``create()``; admission is
never re-run from validated data.  ``child.instance``/``initial_data`` are
restored after every item so the items cannot leak state into each other.
"""
from __future__ import unicode_literals

from collections.abc import Mapping
from copy import copy

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import router, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from rest_framework_bulk.serializers import BulkListSerializer


def apply_nested_scope(serializer, attrs, validated=False):
    """
    E9/R2: make the nested URL parent authoritative for one wire item.

    ``/terms/<term_pk>/children/`` and ``/data-marts/<data_mart_pk>/children/``
    mean "children of the URL node".  A body ``parent_id`` / ``parent__slug``
    may agree with that parent, but it can never re-point the write outside the
    URL scope; the URL value wins and is written as ``parent_id``.

    ``validated=True`` receives a validated-data mapping (values are already
    native); the default receives raw wire data and types only the identity
    fields it needs.
    """
    view = serializer.context.get('view') if getattr(serializer, 'context', None) else None
    raw = getattr(view, 'bulk_scope_parent_raw', None) if view is not None else None
    if raw is None:
        return attrs

    data = dict(attrs)
    model = getattr(getattr(serializer, 'Meta', None), 'model', None)
    fields = getattr(serializer, 'fields', {}) or {}
    parent_field = fields.get('parent_id')
    slug_field = fields.get('parent__slug')

    supplied_parent = data.get('parent_id', empty)
    if supplied_parent is not empty and not validated and parent_field is not None:
        supplied_parent = parent_field.to_internal_value(supplied_parent)

    supplied_slug = data.get('parent__slug', empty)
    if supplied_slug is not empty and not validated and slug_field is not None:
        supplied_slug = slug_field.to_internal_value(supplied_slug)

    if supplied_slug is not empty:
        # The write-only slug is folded into parent_id, never kept alongside it.
        data.pop('parent__slug', None)
        if supplied_slug in (None, ''):
            supplied_slug = empty
        else:
            resolved = None
            if model is not None:
                resolved = model._default_manager.filter(
                    slug=supplied_slug).values_list('pk', flat=True).first()
            if resolved is None:
                raise serializers.ValidationError({
                    'parent__slug': _('The parent slug does not name an existing object.'),
                })
            if supplied_parent is empty:
                supplied_parent = resolved

    getter = getattr(view, 'get_bulk_scope_parent_pk', None)
    scope_pk = getter() if callable(getter) else None
    if scope_pk is None:
        # The URL names a parent that does not exist: a write may not silently
        # fall back to an unscoped create/update.
        if serializer.instance is None or supplied_parent is not empty:
            raise serializers.ValidationError({
                'parent_id': _('The nested URL parent does not name an existing object.'),
            })
        return data

    data['parent_id'] = int(scope_pk)
    return data


class BatchAdmissionPlanItem(object):
    """
    One admitted batch item: typed identity, scoped target and wire data.

    ``identity`` is a tuple of ``(lookup_field, typed_value)`` pairs in
    ``get_id_attrs()`` order.  ``target`` is the admitted model instance or
    ``None`` for a brand-new object.  ``wire`` is the prepared item that the
    child serializer validates (the nested URL scope already applied).
    """

    __slots__ = ('index', 'target', 'identity', 'wire', 'validated')

    def __init__(self, index, target, identity, wire):
        self.index = index
        self.target = target
        self.identity = identity
        self.wire = wire
        self.validated = None

    def __repr__(self):
        return '<BatchAdmissionPlanItem {} target={!r} identity={!r}>'.format(
            self.index, getattr(self.target, 'pk', None), self.identity,
        )


class ScopedBulkAdmissionMixin(object):
    """
    Whole-batch, view-scoped POST/upsert admission for EDW bulk serializers.

    Subclasses declare ``bulk_admission_new_required_fields`` (wire fields that
    a brand-new object must carry, e.g. ``slug``) and optionally
    ``bulk_admission_natural_key`` (the model field used to detect a shadowing
    object outside the permitted scope).
    """

    #: Fields required on a new object.  A lookup field (``id``) is not enough.
    bulk_admission_new_required_fields = ()

    #: Model field whose global existence makes a "new" object ambiguous.
    #: ``None`` for models without a natural key (Entity is identified by pk).
    bulk_admission_natural_key = None

    # ------------------------------------------------------------------ #
    # Batch state
    # ------------------------------------------------------------------ #
    def _reset_batch_state(self):
        self._batch_plan = None
        self._batch_alias = None
        self._batch_scope = None
        self._batch_model = None
        self._batch_view = None
        self._batch_request = None
        self._batch_next_index = 0
        # The provider's update() compares the re-resolved target with the
        # identity recorded during validation; it must exist for updates.
        self._validated_targets = {}

    def to_internal_value(self, data):
        """
        Admit the whole batch first, then run the child state-aware validators.

        ``ListSerializer.to_internal_value`` calls ``run_child_validation`` per
        item in data order; the admission pass below has already resolved and
        authorized every item before the first of those calls, so the two passes
        are strictly separated even though the second one is driven by the
        provider's loop.
        """
        self._reset_batch_state()
        if not isinstance(data, list):
            return super(ScopedBulkAdmissionMixin, self).to_internal_value(data)
        self._admit_complete_batch(data)
        return super(ScopedBulkAdmissionMixin, self).to_internal_value(data)

    # ------------------------------------------------------------------ #
    # Stage 1: whole-batch admission (no child field hooks, no writes)
    # ------------------------------------------------------------------ #
    def _admit_complete_batch(self, data):
        """Resolve and authorize every item; raise before any validator runs."""
        model = self.get_admission_model()
        alias = self.get_write_alias(model)
        scope = self.get_admission_queryset(alias)
        view = self.context.get('view')
        request = getattr(view, 'request', None) or self.context.get('request')

        plans = []
        errors = {}
        seen_targets = {}
        seen_new_lookups = {}
        for index, item in enumerate(data):
            if not isinstance(item, Mapping):
                message = self.child.error_messages['invalid'].format(
                    datatype=type(item).__name__,
                )
                errors[index] = {api_settings.NON_FIELD_ERRORS_KEY: [message]}
                plans.append(None)
                continue
            try:
                prepared = apply_nested_scope(self.child, item)
                identity = self._typed_wire_identity(prepared)
                target = self._admit_one(
                    identity, prepared, index, scope, alias, view, request,
                    seen_targets, seen_new_lookups,
                )
            except serializers.ValidationError as exc:
                errors[index] = exc.detail
                plans.append(None)
                continue
            plans.append(BatchAdmissionPlanItem(index, target, identity, prepared))

        if errors:
            raise serializers.ValidationError(errors)

        self._batch_plan = plans
        self._batch_alias = alias
        self._batch_scope = scope
        self._batch_model = model
        self._batch_view = view
        self._batch_request = request
        return plans

    def _typed_wire_identity(self, data):
        """
        Type only the declared identity fields of one wire item.

        ``Field.to_internal_value`` is the field's own type conversion; the
        serializer-level ``validate_<field>`` hook is *not* called here (that
        hook is part of the state-aware validation pass and may read the
        database).
        """
        identity = []
        fields = getattr(self.child, 'fields', {}) or {}
        for name in self.get_id_attrs():
            value = data.get(name, empty)
            if value is empty or value is None or value == '':
                continue
            field = fields.get(name)
            if field is None:
                raise serializers.ValidationError({
                    name: [_('This identity field is not accepted by the serializer.')],
                })
            try:
                value = self._type_lookup_value(field, value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({name: [str(exc)]})
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({name: exc.detail})
            if value is empty or value is None or value == '':
                continue
            identity.append((name, value))
        return tuple(identity)

    @staticmethod
    def _type_lookup_value(field, value):
        if not field.read_only:
            return field.to_internal_value(value)
        # A read-only field (an auto primary key) is normally skipped by
        # ``run_validation``; the InfLabs contraction makes a shallow writable
        # copy so the supplied identity is still typed, never re-assigned.
        writable = copy(field)
        writable.read_only = False
        return writable.run_validation(value)

    def _validated_identity(self, validated):
        """Native lookup values present in validated data, in lookup order."""
        if not isinstance(validated, Mapping):
            return ()
        return tuple(
            (name, validated[name]) for name in self.get_id_attrs()
            if validated.get(name, empty) not in (empty, None, '')
        )

    # ------------------------------------------------------------------ #
    # Identity / target resolution
    # ------------------------------------------------------------------ #
    def get_id_attrs(self):
        """
        Ordered identity fields of the child serializer.

        EDW serializers carry their identity in ``RESTMeta.lookup_fields``
        exposed by ``get_id_attrs()``; the fallback keeps the provider contract
        for Meta-only serializers.
        """
        child = getattr(self, 'child', None)
        getter = getattr(child, 'get_id_attrs', None)
        if callable(getter):
            return tuple(getter())
        meta = getattr(child, 'Meta', None)
        lookup_fields = getattr(meta, 'lookup_fields', None)
        if lookup_fields is None:
            lookup_fields = getattr(meta, 'update_lookup_field', None)
        if lookup_fields is None:
            lookup_fields = ('id',)
        if isinstance(lookup_fields, str):
            lookup_fields = (lookup_fields,)
        return tuple(lookup_fields)

    def get_admission_model(self):
        """Model of the admitted data (list Meta first, child Meta as fallback)."""
        meta = getattr(self, 'Meta', None)
        model = getattr(meta, 'model', None)
        if model is None:
            child_meta = getattr(getattr(self, 'child', None), 'Meta', None)
            model = getattr(child_meta, 'model', None)
        if model is None:
            raise ImproperlyConfigured(
                'Bulk admission requires an explicit model on the serializer Meta.'
            )
        return model

    def get_write_alias(self, model=None):
        """The single database alias used for both admission and writes."""
        return router.db_for_write(model if model is not None else self.get_admission_model())

    def get_admission_queryset(self, alias):
        """
        The view's own queryset after its filter backends, bound to ``alias``.

        Using the view (not ``Model.objects``) preserves data-mart scoping,
        search parameters and any queryset the concrete view already applies.
        """
        view = self.context.get('view')
        if view is None:
            raise ImproperlyConfigured(
                'Scoped bulk admission requires the DRF view in the serializer context.'
            )
        queryset = view.get_queryset().using(alias)
        queryset = view.filter_queryset(queryset)
        explicit_alias = getattr(queryset, '_db', None)
        if explicit_alias is not None and explicit_alias != alias:
            raise ImproperlyConfigured(
                'Bulk admission queryset is bound to a non-write database alias.'
            )
        if explicit_alias is None:
            queryset = queryset.using(alias)
        return queryset

    def _is_primary_identity(self, name, model):
        return name == model._meta.pk.attname or name == model._meta.pk.name

    def _resolve_identity_matches(self, identity, scope):
        """All scoped matches for the supplied identity pairs."""
        matches = []
        for name, value in identity:
            candidates = list(scope.filter(**{name: value})[:2])
            if len(candidates) > 1:
                raise serializers.ValidationError(
                    _('Bulk identity `{name}` matches more than one object in the '
                      'permitted scope.').format(name=name),
                    code='ambiguous_bulk_identity',
                )
            if candidates:
                matches.append((name, candidates[0]))
        return matches

    def _admit_one(self, identity, data, index, scope, alias, view, request,
                   seen_targets, seen_new_lookups):
        """
        Resolve and authorize one batch item before any write.

        Raises ``serializers.ValidationError`` for identity problems and
        ``rest_framework.exceptions.PermissionDenied`` (through the view check)
        for objects the request may not change.
        """
        model = self.get_admission_model()

        matches = self._resolve_identity_matches(identity, scope)

        distinct = {}
        for name, target in matches:
            distinct[(target._meta.concrete_model, target.pk)] = target

        if len(distinct) > 1 or (distinct and len(matches) != len(identity)):
            raise serializers.ValidationError(
                _('Bulk item {index}: supplied identity fields point to different '
                  'objects or to an object outside the permitted scope.').format(index=index),
                code='ambiguous_bulk_identity',
            )

        if distinct:
            target = next(iter(distinct.values()))
            if target._state.db != alias:
                raise ImproperlyConfigured(
                    'Bulk target is bound to a non-write database alias.'
                )
            target_key = (target._meta.concrete_model, target.pk)
            if target_key in seen_targets:
                raise serializers.ValidationError(
                    _('Bulk item {index}: duplicate target, also addressed by item '
                      '{first}.').format(index=index, first=seen_targets[target_key]),
                    code='duplicate_bulk_target',
                )
            seen_targets[target_key] = index
            if view is not None:
                # Per-object authorization before any write in the batch and
                # before the child's state-aware validators run.
                view.check_object_permissions(request, target)
            return target

        if getattr(self, 'instance', None) is not None:
            # A PUT/PATCH batch identifies existing objects only; it may never
            # fall back to a create.
            raise serializers.ValidationError(
                _('Bulk item {index}: no existing object matches the supplied '
                  'identity.').format(index=index),
                code='unknown_bulk_identity',
            )

        # A supplied primary key that is not part of the permitted scope is a
        # forbidden target when it exists elsewhere and an unknown identity when
        # it does not exist at all.  Neither may be dropped silently.
        for name, value in identity:
            if not self._is_primary_identity(name, model):
                continue
            if model._default_manager.using(alias).filter(**{name: value}).exists():
                raise serializers.ValidationError(
                    _('Bulk item {index}: identity `{name}` is outside the permitted '
                      'scope.').format(index=index, name=name),
                    code='forbidden_bulk_identity',
                )
            raise serializers.ValidationError(
                _('Bulk item {index}: identity `{name}` does not match an existing '
                  'object.').format(index=index, name=name),
                code='unknown_bulk_identity',
            )

        # A brand-new object: the wire data must carry the required fields.
        missing = [
            name for name in self.bulk_admission_new_required_fields
            if data.get(name, empty) in (empty, None, '')
        ]
        if missing:
            raise serializers.ValidationError(
                {missing[0]: [_('A new bulk object requires `{0}`.').format(missing[0])]},
                code='bulk_new_identity_required',
            )

        for name, value in identity:
            lookup_key = (name, value)
            if lookup_key in seen_new_lookups:
                raise serializers.ValidationError(
                    _('Bulk item {index}: duplicate new identity `{name}`, also used '
                      'by item {first}.').format(
                        index=index, name=name, first=seen_new_lookups[lookup_key]),
                    code='duplicate_bulk_identity',
                )
            seen_new_lookups[lookup_key] = index

        natural_key = self.bulk_admission_natural_key
        if natural_key:
            typed = dict(identity)
            natural_value = typed.get(natural_key, data.get(natural_key, empty))
            if natural_value in (empty, None, ''):
                raise serializers.ValidationError(
                    {natural_key: [_('A new bulk object requires `{0}`.').format(natural_key)]},
                    code='bulk_new_identity_required',
                )
            # Existence, not authority: the target may never be modified from
            # here.  Read the same write alias so a stale replica cannot hide an
            # object outside the permitted scope.
            if model._default_manager.using(alias).filter(
                    **{natural_key: natural_value}).exists():
                raise serializers.ValidationError(
                    _('Bulk item {index}: identity `{name}` already exists outside the '
                      'permitted scope.').format(index=index, name=natural_key),
                    code='ambiguous_bulk_identity',
                )

        return None

    # ------------------------------------------------------------------ #
    # Stage 2: child validation with the admitted target bound
    # ------------------------------------------------------------------ #
    def run_child_validation(self, data):
        """
        Validate one *already admitted* item with ``child.instance`` bound.

        Called by the provider's ``ListSerializer.to_internal_value`` loop in
        data order, after ``_admit_complete_batch`` authorized the whole batch.
        """
        plans = getattr(self, '_batch_plan', None)
        if plans is None:
            return super(ScopedBulkAdmissionMixin, self).run_child_validation(data)

        index = self._batch_next_index
        self._batch_next_index = index + 1
        if index >= len(plans) or plans[index] is None:
            raise ImproperlyConfigured(
                'Bulk admission and child validation item order diverged.'
            )
        plan = plans[index]

        if isinstance(data, Mapping):
            try:
                supplied = self._typed_wire_identity(data)
            except serializers.ValidationError:
                supplied = None
            if supplied is not None and supplied != plan.identity:
                raise ImproperlyConfigured(
                    'Bulk validation item {} does not match the admitted item.'.format(index)
                )

        validated = self._validate_admitted_item(plan)
        self._bind_validated_identity(plan, validated)
        plan.validated = validated
        if plan.target is not None and getattr(self, 'instance', None) is not None:
            self._record_validated_target(plan, validated)
        return validated

    def _validate_admitted_item(self, plan):
        child = self.child
        old_instance = getattr(child, 'instance', None)
        old_initial = getattr(child, 'initial_data', empty)
        try:
            # None for a create: real RESTMeta create hooks see the new state;
            # the admitted instance for an update: they never re-resolve it.
            child.instance = plan.target
            child.initial_data = plan.wire
            return child.run_validation(plan.wire)
        finally:
            child.instance = old_instance
            if old_initial is empty:
                child.__dict__.pop('initial_data', None)
            else:
                child.initial_data = old_initial

    def _bind_validated_identity(self, plan, validated):
        """
        The identity admitted before validation must be the identity saved.

        A hook that rewrites a lookup field is refused explicitly instead of
        being resolved again (which is how a retarget used to succeed).
        """
        validated_identity = self._validated_identity(validated)
        if validated_identity != plan.identity:
            raise serializers.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [
                    _('Bulk item {index}: the admitted identity changed during '
                      'validation and the item was refused.').format(index=plan.index),
                ],
            }, code='bulk_identity_changed')
        target = self._resolve_admitted_target(plan.identity, self._batch_scope)
        if plan.target is None:
            if target is not None:
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        _('Bulk item {index}: the admitted new identity now names an '
                          'existing object.').format(index=plan.index),
                    ],
                }, code='bulk_identity_changed')
            return
        if target is None or target.pk != plan.target.pk:
            raise serializers.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [
                    _('Bulk item {index}: the admitted target is no longer the same '
                      'object.').format(index=plan.index),
                ],
            }, code='bulk_identity_changed')

    def _resolve_admitted_target(self, identity, scope):
        """Resolve the admitted identity inside the admission scope."""
        if not identity:
            return None
        matches = self._resolve_identity_matches(identity, scope)
        distinct = {}
        for name, target in matches:
            distinct[(target._meta.concrete_model, target.pk)] = target
        if not matches:
            return None
        if len(distinct) != 1 or len(matches) != len(identity):
            raise serializers.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [
                    _('The admitted identity no longer resolves to exactly one object.'),
                ],
            }, code='bulk_identity_changed')
        return next(iter(distinct.values()))

    def _record_validated_target(self, plan, validated):
        lookup = self._validated_identity(validated)
        if not lookup:
            return
        name, value = lookup[0]
        self._validated_targets[(name, value)] = (
            self._batch_alias, plan.target._meta.concrete_model, plan.target.pk,
        )

    # ------------------------------------------------------------------ #
    # Admission policy (the provider's non-empty hook)
    # ------------------------------------------------------------------ #
    def validate_bulk_create(self, validated_data):
        """
        Admit the complete POST batch before the first write.

        ``create()`` consumes the plan produced by ``to_internal_value`` and
        never calls this hook; it stays here as the documented consumer-policy
        marker the provider requires, and as the explicit admission entry point
        for callers that hand it validated data directly.
        """
        plan = getattr(self, '_batch_plan', None)
        if plan is not None and len(plan) == len(validated_data):
            return
        self._reset_batch_state()
        self._admit_complete_batch(list(validated_data))

    def _build_bulk_admission(self, validated_data):
        """Backwards-compatible alias for the admission pass."""
        return self._admit_complete_batch(list(validated_data))

    # ------------------------------------------------------------------ #
    # Scoped create/upsert
    # ------------------------------------------------------------------ #
    def _require_batch_plan(self, count):
        plans = getattr(self, '_batch_plan', None)
        if plans is None or len(plans) != count:
            raise ImproperlyConfigured(
                'Bulk create requires the whole-batch admission plan produced by '
                'to_internal_value(); admission is never re-run from validated data.'
            )
        return plans

    def _recheck_batch_before_write(self, plans, alias):
        """
        Re-check permissions and identity stability immediately before a write.

        Runs inside the single write transaction, after every hook/validator and
        before the first row change.
        """
        scope = self._batch_scope
        view = self._batch_view
        request = self._batch_request
        model = self._batch_model
        natural_key = self.bulk_admission_natural_key

        for plan in plans:
            target = self._resolve_admitted_target(plan.identity, scope)
            if plan.target is None:
                if target is not None:
                    raise serializers.ValidationError({
                        api_settings.NON_FIELD_ERRORS_KEY: [
                            _('Bulk item {index}: the admitted new identity now names '
                              'an existing object.').format(index=plan.index),
                        ],
                    }, code='bulk_identity_changed')
                if natural_key:
                    typed = dict(plan.identity)
                    natural_value = typed.get(natural_key, plan.wire.get(natural_key, empty))
                    if natural_value not in (empty, None, '') and \
                            model._default_manager.using(alias).filter(
                                **{natural_key: natural_value}).exists():
                        raise serializers.ValidationError({
                            api_settings.NON_FIELD_ERRORS_KEY: [
                                _('Bulk item {index}: the new natural key was created '
                                  'after admission.').format(index=plan.index),
                            ],
                        }, code='bulk_identity_changed')
                continue

            if target is None or target.pk != plan.target.pk:
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        _('Bulk item {index}: the admitted target is no longer the same '
                          'object.').format(index=plan.index),
                    ],
                }, code='bulk_identity_changed')
            if plan.target._state.db != alias:
                raise ImproperlyConfigured(
                    'Bulk target is bound to a non-write database alias.'
                )
            if not model._default_manager.using(alias).filter(pk=plan.target.pk).exists():
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        _('Bulk item {index}: the admitted target no longer exists.'
                          ).format(index=plan.index),
                    ],
                }, code='bulk_identity_changed')
            if view is not None:
                view.check_object_permissions(request, plan.target)

    def create(self, validated_data):
        """
        Apply the admitted plan: create new objects, update admitted targets.

        The plan resolved before validation is the only authority.  The
        provider's default ``create`` loop calls ``child.create()`` for every
        item; with lookup retention that would delegate upsert authority to the
        child (and thus to the global manager).  Identity fields are never
        re-assigned on update and a create never carries a supplied primary key.
        """
        model = self.get_admission_model()
        alias = self.get_write_alias(model)
        plans = self._require_batch_plan(len(validated_data))
        with transaction.atomic(using=alias):
            self._recheck_batch_before_write(plans, alias)
            instances = []
            for plan, attrs in zip(plans, validated_data):
                payload = dict(attrs)
                for name in self.get_id_attrs():
                    if plan.target is not None or self._is_primary_identity(name, model):
                        payload.pop(name, None)
                if plan.target is None:
                    instances.append(self.child.create(payload))
                else:
                    instances.append(self.child.update(plan.target, payload))
            return instances


__all__ = ['BatchAdmissionPlanItem', 'ScopedBulkAdmissionMixin', 'apply_nested_scope']
