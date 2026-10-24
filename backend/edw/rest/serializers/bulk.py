# -*- coding: utf-8 -*-
"""
E7: scoped admission for bulk POST/upsert on the real InfLabs bulk API.

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
"""
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db import router, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import empty

from rest_framework_bulk.serializers import BulkListSerializer


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

    # ------------------------------------------------------------------ #
    # Admission policy (the provider's non-empty hook)
    # ------------------------------------------------------------------ #
    def validate_bulk_create(self, validated_data):
        """
        Admit or refuse the complete POST batch before the first write.

        Raises ``serializers.ValidationError`` for identity problems and
        ``rest_framework.exceptions.PermissionDenied`` (through the view check)
        for objects the request may not change.
        """
        self._bulk_admission_plan = self._build_bulk_admission(validated_data)

    def _build_bulk_admission(self, validated_data):
        model = self.get_admission_model()
        alias = self.get_write_alias(model)
        scope = self.get_admission_queryset(alias)
        view = self.context.get('view')
        request = getattr(view, 'request', None) or self.context.get('request')
        lookup_fields = self.get_id_attrs()

        plan = []
        seen_targets = {}
        seen_new_lookups = {}

        for index, attrs in enumerate(validated_data):
            matches = []
            supplied = []
            for name in lookup_fields:
                value = attrs.get(name, empty)
                if value is empty or value is None or value == '':
                    continue
                supplied.append((name, value))
                candidates = list(scope.filter(**{name: value})[:2])
                if len(candidates) > 1:
                    raise serializers.ValidationError(
                        _('Bulk item {index}: identity `{name}` matches more than one '
                          'object in the permitted scope.').format(index=index, name=name),
                        code='ambiguous_bulk_identity',
                    )
                if candidates:
                    matches.append((name, candidates[0]))

            distinct = {}
            for name, target in matches:
                distinct[(target._meta.concrete_model, target.pk)] = target

            if len(distinct) > 1 or (distinct and len(matches) != len(supplied)):
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
                    # Per-object authorization before any write in the batch.
                    view.check_object_permissions(request, target)
                plan.append((target, dict(attrs)))
                continue

            # A brand-new object: the wire data must carry the natural key.
            missing = [
                name for name in self.bulk_admission_new_required_fields
                if attrs.get(name, empty) in (empty, None, '')
            ]
            if missing:
                raise serializers.ValidationError(
                    {missing[0]: [_('A new bulk object requires `{0}`.').format(missing[0])]},
                    code='bulk_new_identity_required',
                )

            for name, value in supplied:
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
                natural_value = attrs.get(natural_key, empty)
                if natural_value in (empty, None, ''):
                    raise serializers.ValidationError(
                        {natural_key: [_('A new bulk object requires `{0}`.').format(natural_key)]},
                        code='bulk_new_identity_required',
                    )
                # Existence, not authority: the target may never be modified
                # from here.  Read the same write alias so a stale replica
                # cannot hide an object outside the permitted scope.
                if model._default_manager.using(alias).filter(
                        **{natural_key: natural_value}).exists():
                    raise serializers.ValidationError(
                        _('Bulk item {index}: identity `{name}` already exists outside the '
                          'permitted scope.').format(index=index, name=natural_key),
                        code='ambiguous_bulk_identity',
                    )

            plan.append((None, dict(attrs)))

        return plan

    # ------------------------------------------------------------------ #
    # Scoped create/upsert
    # ------------------------------------------------------------------ #
    def create(self, validated_data):
        """
        Apply the admitted plan: create new objects, update admitted targets.

        The provider's default ``create`` loop calls ``child.create()`` for every
        item; with lookup retention that would delegate upsert authority to the
        child (and thus to the global manager).  The plan resolved here is the
        only authority.  Identity fields are never re-assigned on update.
        """
        model = self.get_admission_model()
        alias = self.get_write_alias(model)
        with transaction.atomic(using=alias):
            self.validate_bulk_create(validated_data)
            instances = []
            for target, attrs in self._bulk_admission_plan:
                payload = dict(attrs)
                if target is None:
                    payload.pop('id', None)
                    instances.append(self.child.create(payload))
                else:
                    for name in self.get_id_attrs():
                        payload.pop(name, None)
                    instances.append(self.child.update(target, payload))
            return instances


__all__ = ['ScopedBulkAdmissionMixin']
