# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types

from django.db.models.base import ModelBase
from django.utils.module_loading import import_string

from rest_framework import serializers
from rest_framework import exceptions

import rest_framework_filters as filters


class RESTOptions(object):
    """
    Options class for REST models. Use this as an inner class called ``RESTMeta``::

        class MyModel(Model):
            class RESTMeta:
                exclude = ['name']
                filters = {
                    'published_at': filters.IsoDateTimeFilter(
                        name='published_at', lookup_expr='exact'),
                    'close_at': ('filters.IsoDateTimeFilter', {
                        'name': 'close_at',
                        'lookup_expr': 'exact',
                        # 'action': lambda qs, value: qs
                        }),
                        'is_id__in__18_19': ('rest_framework_filters.MethodFilter', {
                        })
                }

                def filter_is_id__in__18_19(self, name, qs, value):
                    return qs.filter(id__in=[18, 19])

                def filter_queryset(self, request, queryset, view):
                    # if view.action == 'list':
                    #    pass
                    return queryset

    """

    exclude = []
    include = {}
    permission_classes = []
    filters = {}

    def __init__(self, opts=None, **kwargs):
        # Override defaults with options provided
        if opts:
            opts = list(opts.__dict__.items())
        else:
            opts = []
        opts.extend(list(kwargs.items()))

        for key, value in opts:
            if key[:2] == '__':
                continue
            setattr(self, key, value)

    def __iter__(self):
        return ((k, v) for k, v in self.__dict__.items() if k[0] != '_')


class RESTModelBase(ModelBase):
    """
    Metaclass for REST models
    """
    def __new__(cls, name, bases, attrs):
        """
        Create subclasses of Model. This:
         - adds the RESTMeta fields to the class
        """
        new = super(RESTModelBase, cls).__new__(cls, name, bases, attrs)
        # Grab `Model.RESTMeta`, and rename it `_rest_meta`
        RESTMeta = attrs.pop('RESTMeta', None)
        if not RESTMeta:
            class RESTMeta:
                pass

        initial_options = frozenset(dir(RESTMeta))

        # extend RESTMeta from base classes
        for base in bases:
            if hasattr(base, '_rest_meta'):
                for name, value in base._rest_meta:
                    if name not in initial_options:
                        setattr(RESTMeta, name, value)
        setattr(new, '_rest_meta', RESTOptions(RESTMeta))

        return new


class DynamicFieldsSerializerMixin(object):

    def __init__(self, *args, **kwargs):
        instance = args[0] if args else None
        if instance is not None and hasattr(instance, '_rest_meta'):
            rest_meta = instance._rest_meta
        else:
            rest_meta = getattr(self.Meta.model, '_rest_meta', None)
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)
        if rest_meta:
            remove_fields, include_fields = rest_meta.exclude, rest_meta.include
            for field_name, field in include_fields.items():
                if isinstance(field, (tuple, list)):
                    field = import_string(field[0])(**field[1])
                if isinstance(field, serializers.SerializerMethodField):
                    default_method_name = 'get_{field_name}'.format(field_name=field_name)
                    if field.method_name is None:
                        method_name = default_method_name
                    else:
                        method_name = field.method_name
                        # hack for SerializerMethodField.bind method
                        if field.method_name == default_method_name:
                            field.method_name = None
                    method = getattr(rest_meta, method_name)
                    setattr(self, method_name, types.MethodType(method, self, self.__class__))
                elif isinstance(field, serializers.ListField):
                    # hack for ListField.__init__ method
                    field.child.source = None
                elif getattr(field, 'many', False):
                    # hack for `many=True`
                    field.source = None
                self.fields[field_name] = field
            for field_name in remove_fields:
                self.fields.pop(field_name)


class CheckPermissionsSerializerMixin(object):

    def __init__(self, *args, **kwargs):
        instance = args[0] if args else None
        self._permissions_cache = None if instance is not None else {}
        super(CheckPermissionsSerializerMixin, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_permissions(permission_classes):
        """
        Instantiates and returns the list of permissions that view requires.
        """
        return [permission() for permission in permission_classes]

    def permission_denied(self, request, message=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(detail=message)

    def to_representation(self, data):
        """
        Check permissions
        """
        if hasattr(data, '_rest_meta'):
            context = self.context
            request = context.get('request', None)

            assert request is not None, (
                "'%s' `.__init__()` method parameter `context` should include a `request` attribute."
                % self.__class__.__name__
            )

            view = context.get('view')

            if self._permissions_cache is None:
                """
                Check if the request should be permitted for a given object.
                Raises an appropriate exception if the request is not permitted.
                """
                permission_classes = data._rest_meta.permission_classes

                for permission in self._get_permissions(permission_classes):
                    if not permission.has_object_permission(request, view, data):
                        self.permission_denied(
                            request, message=getattr(permission, 'message', None)
                        )
            else:
                """
                Check if the request should be permitted.
                Raises an appropriate exception if the request is not permitted.
                """
                permission_classes = self._permissions_cache.get(data.__class__, None)

                if permission_classes is None:
                    permission_classes = data._rest_meta.permission_classes

                    for permission in self._get_permissions(permission_classes):
                        if not permission.has_permission(request, view):
                            self.permission_denied(
                                request, message=getattr(permission, 'message', None)
                            )

                    self._permissions_cache[data.__class__] = permission_classes

        return super(CheckPermissionsSerializerMixin, self).to_representation(data)


class DynamicFilterSetMixin(object):

    def __new__(cls, data=None, queryset=None, **kwargs):
        it = super(DynamicFilterSetMixin, cls).__new__(cls, data=data, queryset=queryset, **kwargs)
        it._extra_method_filters = {}
        if data:
            data_mart = data['_data_mart']
            entity_model = data_mart.entities_model if data_mart is not None else queryset.model
            it._rest_meta = rest_meta = getattr(entity_model, '_rest_meta', None)
            if rest_meta:
                for filter_name, filter_ in rest_meta.filters.items():
                    if isinstance(filter_, (tuple, list)):
                        filter_ = import_string(filter_[0])(**filter_[1])

                    if isinstance(filter_, filters.MethodFilter):
                        method_name = 'filter_{0}'.format(filter_name)
                        filter_.action = method_name
                        it._extra_method_filters[method_name] = getattr(rest_meta, method_name)
                    else:
                        assert filter_.name, 'Expected `name` argument in `{0}` filter constructor of {1} class'.format(
                            filter_name, filter_.__class__.__name__)

                    it.base_filters[filter_name] = filter_
        return it

    def __init__(self, *arg, **kwargs):
        for method_name, method in self._extra_method_filters.items():
            setattr(self, method_name, types.MethodType(method, self, self.__class__))
        super(DynamicFilterSetMixin, self).__init__(*arg, **kwargs)


class DynamicFilterMixin(object):
    dynamic_filter_set_class = None

    def __init__(self):
        assert self.dynamic_filter_set_class, \
            'Using DynamicFilterMixin, but `dynamic_filter_set_class` is is not defined'

    def filter_queryset(self, request, queryset, view):
        self.dynamic_filter_set = self.dynamic_filter_set_class(request.GET, queryset)

        queryset = self.dynamic_filter_set.qs

        # add extra `filter_queryset` from RESTMeta
        rest_meta = getattr(self.dynamic_filter_set, '_rest_meta', None)
        if rest_meta:
            filter_qs = getattr(rest_meta, 'filter_queryset', None)
            if filter_qs:
                setattr(self, '_extra_filter_queryset',
                        types.MethodType(filter_qs, self, self.__class__))
                queryset = self._extra_filter_queryset(request, queryset, view)

        return queryset
