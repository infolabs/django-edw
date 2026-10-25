# -*- coding: utf-8 -*-

from functools import wraps

from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.deletion import Collector, ProtectedError
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from edw.rest.permissions import get_data_mart_permissions


class DeleteEffectSetError(Exception):
    """E11/R4: the deletion effect set could not be measured; refuse the delete."""


def remove_empty_params_from_request(exclude=None):
    """
    ENG: Remove empty query params from request
    RUS: Удаляет пустые параметры из запроса
    """
    if exclude is None:
        exclude = []

    def remove_empty_params_from_request_decorator(func):
        """
         RUS: Удаляет пустые параметры из запроса в результате применения декоратора
        """
        @wraps(func)
        def func_wrapper(self, request, *args, **kwargs):
            """
            Функция-обертка
            """
            query_params = request.GET.copy()
            for k, v in list(query_params.items()):
                if v == '' and k not in exclude:
                    del query_params[k]
            request.GET = query_params
            return func(self, request, *args, **kwargs)
        return func_wrapper
    return remove_empty_params_from_request_decorator


def enforce_url_scope(request, param, value, label):
    """
    E9: make a nested URL scope authoritative for the whole request.

    A nested route (``/terms/<term_pk>/children/``,
    ``/data-marts/<data_mart_pk>/terms/``) already names the parent scope.  A
    query-string value may narrow that scope but never replace it; a conflicting
    value is refused explicitly instead of silently re-pointing the request.

    The query dict of the *underlying* Django request is updated (DRF
    ``request.query_params`` reads it), so filter backends and bulk admission see
    the same mandatory scope.
    """
    underlying = getattr(request, '_request', request)
    data = underlying.GET
    current = data.get(param)
    if current not in (None, '') and str(current) != str(value):
        raise ValidationError({
            param: _(
                'The URL %(label)s scope cannot be overridden or replaced by the '
                'query string.'
            ) % {'label': label},
        })
    if not getattr(data, '_mutable', True):
        data = data.copy()
        underlying.GET = data
    data[param] = str(value)
    return data


def _request_query_data(request):
    data = getattr(request, 'query_params', None)
    if data is None:
        data = getattr(request, 'GET', None)
    return data if data is not None else {}


class SingleWriteAliasGuardMixin(object):
    """
    E9/E11-R5: one write database alias for the whole validation/write chain.

    The InfLabs bulk unit already refuses cross-database queries, but the EDW
    models open their own ``transaction.atomic()`` and the state-aware
    validators read through ``db_for_read``.  A read router that points at a
    replica would therefore move validation away from the row that is about to
    be written (and trip the provider guard halfway through the unit).

    EDW does not promise distributed atomicity.  When the read and write routers
    disagree for the model, bulk writes are refused *before* any validator and
    before the first write; when they agree, that single alias is used for the
    complete chain.

    E11 extends the same contract to the detail PUT/PATCH/DELETE methods.  The
    authority is computed before validators and before the first write from the
    class-level router answers *and* the instance hints: a queryset bound to
    ``.using()``, a ``write=None`` router whose instance hint moves the write to
    another alias, or an object whose ``_state.db`` differs from the write alias
    are all refused instead of silently writing another database.  The refusal
    is a 400 with an explicit reason (the connector is misconfigured; no alias
    may receive a partial unit).
    """

    def _write_alias_problem(self, model, queryset=None, instance=None):
        """Return a human-readable reason why the alias chain is not one alias."""
        class_write = router.db_for_write(model) or DEFAULT_DB_ALIAS
        class_read = router.db_for_read(model) or DEFAULT_DB_ALIAS
        if class_read != class_write:
            return (
                'db_for_read({model})={read!r} but db_for_write({model})={write!r}.'
            ).format(model=model.__name__, read=class_read, write=class_write)
        if queryset is not None:
            explicit = getattr(queryset, '_db', None)
            if explicit is not None and explicit != class_write:
                return (
                    'the queryset is bound to {explicit!r} but db_for_write({model})'
                    '={write!r}.'
                ).format(explicit=explicit, model=model.__name__, write=class_write)
        if instance is not None:
            state_db = instance._state.db
            if state_db is not None and state_db != class_write:
                return (
                    'the instance is loaded from {state!r} but db_for_write({model})'
                    '={write!r}.'
                ).format(state=state_db, model=model.__name__, write=class_write)
            hinted_write = router.db_for_write(model, instance=instance) or DEFAULT_DB_ALIAS
            if hinted_write != class_write:
                return (
                    'a db_for_write instance hint selects {hinted!r} while the '
                    'model-level write alias is {write!r}.'
                ).format(hinted=hinted_write, write=class_write)
            hinted_read = router.db_for_read(model, instance=instance) or DEFAULT_DB_ALIAS
            if hinted_read != class_read:
                return (
                    'a db_for_read instance hint selects {hinted!r} while the '
                    'model-level read alias is {read!r}.'
                ).format(hinted=hinted_read, read=class_read)
        return None

    def get_bulk_write_alias(self):
        queryset = self.get_queryset()
        problem = self._write_alias_problem(queryset.model, queryset=queryset)
        if problem is not None:
            raise ImproperlyConfigured(
                'Bulk writes require one database alias for validation and writes: '
                + problem
            )
        return router.db_for_write(queryset.model) or DEFAULT_DB_ALIAS

    def _refuse_detail_write(self, action, problem):
        raise ValidationError({
            'detail': _(
                'The %(action)s is refused: this write is not pinned to a single '
                'database alias (%(problem)s)'
            ) % {'action': action, 'problem': problem},
        })

    def _detail_write_instance(self, action):
        """
        Return the admitted detail instance or refuse before any validator/write.

        The model/queryset-level alias is checked before the object is loaded, so
        a divergent read router cannot turn the refusal into a misleading 404;
        the instance hints (``write=None`` + ``instance=...``, ``_state.db``)
        are checked on the loaded object.
        """
        queryset = self.get_queryset()
        problem = self._write_alias_problem(queryset.model, queryset=queryset)
        if problem is not None:
            self._refuse_detail_write(action, problem)
        instance = self.get_object()
        problem = self._write_alias_problem(
            type(instance), queryset=queryset, instance=instance,
        )
        if problem is not None:
            self._refuse_detail_write(action, problem)
        return instance

    def create(self, request, *args, **kwargs):
        self.get_bulk_write_alias()
        return super(SingleWriteAliasGuardMixin, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._detail_write_instance('update')
        return super(SingleWriteAliasGuardMixin, self).update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._detail_write_instance('partial update')
        return super(SingleWriteAliasGuardMixin, self).partial_update(
            request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._detail_write_instance('delete')
        return super(SingleWriteAliasGuardMixin, self).destroy(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        self.get_bulk_write_alias()
        return super(SingleWriteAliasGuardMixin, self).bulk_update(request, *args, **kwargs)

    def bulk_destroy(self, request, *args, **kwargs):
        self.get_bulk_write_alias()
        return super(SingleWriteAliasGuardMixin, self).bulk_destroy(request, *args, **kwargs)


class BulkDestroyPolicyMixin(object):
    """
    E7/E9: explicit, default-deny policy for (bulk and detail) DELETE.

    The InfLabs bulk mixin asks ``allow_bulk_destroy(qs, filtered)`` before it
    touches a single object and its own default is ``False``.  EDW must not
    turn that default into an allow by delegating to the view's root
    permission class: a superuser still has to name an explicit, bounded scope,
    protected tree nodes are never deleted through a cascade, and a data-mart
    entity delete additionally requires the data mart's own ``can_delete``
    grant.

    E9 adds two rules:

    * a scope parameter only counts when the view's filterset really declares it
      and when the filtered result is exactly the declared filtered set -- an
      unknown, ignored or empty parameter can never widen a DELETE to the whole
      collection (R1);
    * the complete deletion effect set (related CASCADE rows and the MPTT
      subtree) must consist only of explicitly named objects; anything else is
      refused by default (R4).

    A subclass opts in by overriding ``allow_bulk_destroy`` and using these
    helpers; the base implementation always refuses.
    """

    #: Query parameters that bound a collection DELETE to a concrete subset.
    bulk_destroy_scope_params = ()

    #: E9: when true, a scope parameter must be declared by ``filterset_class``
    #: and the filtered set must be reproduced by a fresh filterset.
    bulk_destroy_requires_declared_filters = False

    #: Non-filter query parameters that DRF itself consumes.
    bulk_destroy_allowed_non_filter_params = ('format',)

    def allow_bulk_destroy(self, qs, filtered):
        """Default deny; concrete views must opt in explicitly."""
        return False

    def _bulk_destroy_query_data(self):
        return _request_query_data(getattr(self, 'request', None))

    def _bulk_destroy_scope_values(self):
        values = {}
        query_params = self._bulk_destroy_query_data()
        if query_params is None:
            query_params = {}
        kwargs = getattr(self, 'kwargs', {}) or {}
        for name in self.bulk_destroy_scope_params:
            value = query_params.get(name)
            if value in (None, ''):
                value = kwargs.get(name)
            if value not in (None, ''):
                values[name] = value
        return values

    def _has_explicit_bulk_destroy_scope(self, filtered=None):
        if not self._bulk_destroy_scope_values():
            return False
        if not self.bulk_destroy_requires_declared_filters:
            return True
        return self._bulk_destroy_scope_is_applied(filtered)

    def _bulk_destroy_declared_filters(self):
        filterset_class = getattr(self, 'filterset_class', None)
        if filterset_class is None:
            return set()
        return set(getattr(filterset_class, 'base_filters', None) or ())

    def _bulk_destroy_scope_is_applied(self, filtered):
        """
        A DELETE scope is real only if the filterset declares every supplied
        parameter and a fresh filterset reproduces exactly the filtered set.
        """
        filterset_class = getattr(self, 'filterset_class', None)
        if filterset_class is None:
            return False
        declared = self._bulk_destroy_declared_filters()
        if not declared:
            return False
        data = self._bulk_destroy_query_data()
        provided = {name for name, value in data.items() if value not in (None, '')}
        unknown = provided - declared - set(self.bulk_destroy_allowed_non_filter_params)
        if unknown:
            return False
        scope_names = set(self.bulk_destroy_scope_params) & declared
        if not scope_names or not (provided & scope_names):
            return False

        try:
            filterset = filterset_class(
                data=data,
                queryset=self.get_queryset(),
                request=getattr(self, 'request', None),
            )
        except Exception:
            return False
        is_valid = getattr(filterset, 'is_valid', None)
        if callable(is_valid) and not is_valid():
            return False
        cleaned = getattr(getattr(filterset, 'form', None), 'cleaned_data', None) or {}
        applied = {
            name for name, value in cleaned.items()
            if value not in (None, '', [], ())
        }
        if not (applied & scope_names):
            return False

        if filtered is not None:
            try:
                expected = set(filterset.qs.values_list('pk', flat=True))
                actual = set(filtered.values_list('pk', flat=True))
            except Exception:
                return False
            if expected != actual:
                return False
        return True

    def _bulk_destroy_targets_are_explicit(self, filtered):
        """
        Every target must be deletable without an implicit cascade.

        Terms and data marts use MPTT: deleting a parent would cascade to
        descendants that were never named in the request, so only leaves are
        accepted.  Objects carrying the model's ``delete_restriction`` bit are
        refused as well (the ORM would silently skip them, reporting a partial
        success).
        """
        if not filtered.exists():
            return False
        for obj in filtered:
            system_flags = getattr(obj, 'system_flags', None)
            if getattr(system_flags, 'delete_restriction', False):
                return False
            is_leaf_node = getattr(obj, 'is_leaf_node', None)
            if callable(is_leaf_node) and not is_leaf_node():
                return False
        return True

    def _delete_cascade_objects(self, objects):
        """
        E9/E11-R4: objects that a DELETE of ``objects`` would remove implicitly.

        The database ORM collector is the only authority on the effect set.  It
        reports MPTT subtree children, every related ``on_delete=CASCADE`` row
        and *auto-created M2M through rows*: membership bookkeeping is a real
        row change in another model (a shared term would silently lose its
        foreign data-mart membership), so it belongs to the effect set and is
        refused by default like any other implicit consequence.

        The set is fail-closed: if a part of the effect set cannot be counted
        (an exception, not only a positive count), the delete is refused before
        any row is removed.  A failed count is never treated as "0 rows".
        """
        objects = list(objects)
        if not objects:
            return []
        alias = objects[0]._state.db
        if alias is None:
            alias = router.db_for_write(objects[0]._meta.concrete_model) or DEFAULT_DB_ALIAS
        collector = Collector(using=alias)
        collector.collect(objects)
        named = set(objects)
        extra = []
        for related_model, instances in collector.data.items():
            for obj in instances:
                if obj in named:
                    continue
                extra.append(obj)
        # Django's collector may push related rows into ``fast_deletes``
        # (their model has no signals and no own cascade); those rows are
        # still part of the deletion effect set and must be authorized.  The
        # rows themselves are materialised so the policy can name them (for an
        # auto-created M2M through row that is a real other-model row).
        for queryset in collector.fast_deletes:
            related_model = getattr(queryset, 'model', None)
            if related_model is None:
                continue
            try:
                rows = list(queryset)
            except Exception as exc:
                raise DeleteEffectSetError(
                    'The deletion effect set of {} could not be measured; the delete '
                    'is refused.'.format(related_model._meta.label_lower),
                ) from exc
            for row in rows:
                if row in named:
                    continue
                extra.append(row)
        return extra

    def _delete_effect_is_allowed(self, obj):
        """
        Per-consequence DELETE policy; the base implementation is default-deny.

        A subclass may name a consequence that the request itself authorizes
        (for example an M2M through row whose foreign side is named by the URL
        scope).  Anything else is refused.
        """
        return False

    def _delete_effect_is_explicit(self, extra):
        return all(self._delete_effect_is_allowed(obj) for obj in extra)

    def _bulk_destroy_effect_is_explicit(self, filtered):
        try:
            objects = list(filtered)
        except Exception:
            return False
        if not objects:
            return False
        try:
            extra = self._delete_cascade_objects(objects)
        except ProtectedError:
            return False
        except Exception:
            return False
        return self._delete_effect_is_explicit(extra)

    def perform_destroy(self, instance):
        """
        E9/R4: a detail DELETE authorizes only the named object.

        Root/superuser/data-mart grants do not cover descendants or related
        CASCADE rows, so a delete whose ORM effect set is larger than the named
        instance is refused before any row is removed.  Per-object callbacks are
        preserved: subclasses keep overriding ``perform_destroy`` and calling
        ``super()``.
        """
        try:
            extra = self._delete_cascade_objects([instance])
        except ProtectedError:
            raise ValidationError({
                'detail': _('DELETE is refused: protected related objects exist.'),
            })
        except DeleteEffectSetError as exc:
            raise ValidationError({'detail': str(exc)})
        except Exception:
            raise ValidationError({
                'detail': _('DELETE is refused: the deletion effect set could not be '
                            'verified.'),
            })
        if not self._delete_effect_is_explicit(extra):
            raise ValidationError({
                'detail': _(
                    'DELETE is refused: the deletion effect set includes related '
                    'objects that were not explicitly named.'
                ),
            })
        return super(BulkDestroyPolicyMixin, self).perform_destroy(instance)

    def _bulk_destroy_data_mart_grant(self):
        """
        The data-mart grant is a deny-by-default mapping put in GET by
        ``EntityViewSet.check_permissions``; a query-string value is not a grant.
        """
        permissions = get_data_mart_permissions(self.request)
        return permissions if isinstance(permissions, dict) else None


class CustomSerializerViewSetMixin(object):
    """
    Сериалайзер для запросов
    """
    def get_serializer_class(self):
        """
        ENG: Return the class to use for serializer w.r.t to the request method.
        RUS: Возвращает класс для использования сериалайзера к методу запроса
        """
        try:
            return self.custom_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CustomSerializerViewSetMixin, self).get_serializer_class()
