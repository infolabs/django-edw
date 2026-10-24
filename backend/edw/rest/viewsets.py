# -*- coding: utf-8 -*-

from functools import wraps

from edw.rest.permissions import get_data_mart_permissions


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


class BulkDestroyPolicyMixin(object):
    """
    E7: explicit, default-deny policy for collection-level DELETE.

    The InfLabs bulk mixin asks ``allow_bulk_destroy(qs, filtered)`` before it
    touches a single object and its own default is ``False``.  EDW must not
    turn that default into an allow by delegating to the view's root
    permission class: a superuser still has to name an explicit, bounded scope,
    protected tree nodes are never deleted through a cascade, and a data-mart
    entity delete additionally requires the data mart's own ``can_delete``
    grant.

    A subclass opts in by overriding ``allow_bulk_destroy`` and using these
    helpers; the base implementation always refuses.
    """

    #: Query parameters that bound a collection DELETE to a concrete subset.
    bulk_destroy_scope_params = ()

    def allow_bulk_destroy(self, qs, filtered):
        """Default deny; concrete views must opt in explicitly."""
        return False

    def _bulk_destroy_scope_values(self):
        values = {}
        query_params = getattr(self.request, 'query_params', None)
        if query_params is None:
            query_params = getattr(self.request, 'GET', {})
        kwargs = getattr(self, 'kwargs', {}) or {}
        for name in self.bulk_destroy_scope_params:
            value = query_params.get(name)
            if value in (None, ''):
                value = kwargs.get(name)
            if value not in (None, ''):
                values[name] = value
        return values

    def _has_explicit_bulk_destroy_scope(self):
        return bool(self._bulk_destroy_scope_values())

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
