# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types

from django.db.models.base import ModelBase
from django.utils.module_loading import import_string
from django.utils.functional import cached_property

from rest_framework import serializers
from rest_framework import exceptions

import rest_framework_filters as filters


class RESTOptions(object):
    """
    Options class for REST models. Use this as an inner class called ``RESTMeta``::

        class MyModel(Model):
            class RESTMeta:
                exclude = ['name']

                include = {
                    'test_id': ('rest_framework.serializers.IntegerField', {
                        'write_only': True
                    }),
                }

                filters = {
                    'published_at': filters.IsoDateTimeFilter(
                        name='published_at', lookup_expr='exact'),
                    'close_at': ('rest_framework_filters.IsoDateTimeFilter', {
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

                validators = []

                def create(self, validated_data):
                    test_id = validated_data.pop('test_id', None)
                    # print ("Get test_id", test_id)
                    instance = super(self.__class__, self).create(validated_data)
                    # print("Created instance", instance)
                    return instance

                def update(self, instance, validated_data):
                    test_id = validated_data.pop('test_id', None)
                    # print ("Get test_id", test_id)
                    instance = super(self.__class__, self).update(instance, validated_data)
                    # print("Updated instance", self.partial, instance)
                    return instance

                def validate_key(self, value):
                    # print ("+ Validate key +", value)
                    if 'x' not in value.lower():
                        raise serializers.ValidationError("Key must have `x`")
                    return value

                def validate(self, data):
                    try:
                        ControllerActivity.objects.get(key=data['key'])
                    except ControllerActivity.DoesNotExist:
                        raise serializers.ValidationError(_('Invalid controller key'))
                    return data

                group_by = ['particularproblem__name', 'is_solved']

                def get_group_by(self):
                    if self.data_mart is not None and self.queryset.count() <= self.data_mart.limit:
                        return []
                    return self.group_by

    """

    exclude = []
    include = {}

    permission_classes = []

    lookup_fields = ('id',)

    filters = {}

    create = None
    update = None
    validate = None

    validators = None

    _fields_validators = []

    group_by = []
    get_group_by = None

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

        opts = RESTOptions(RESTMeta)

        # parce fields validator
        include_fields = opts.include.copy()
        for field_name in [field.name for field in new._meta.fields]:
            include_fields[field_name] = None
        for field_name in opts.exclude:
            include_fields.pop(field_name, None)
        field_level_validators_names = ["validate_{}".format(field_name) for field_name in include_fields.keys()]

        fields_validators = []
        for name in field_level_validators_names:
            validator = getattr(opts, name, None)
            if validator is not None:
                fields_validators.append(name)
        opts._fields_validators = fields_validators

        setattr(new, '_rest_meta', opts)
        return new


class RESTMetaSerializerMixin(object):

    def __init__(self, *args, **kwargs):
        instance = args[0] if args else None
        if instance is not None and hasattr(instance, '_rest_meta'):
            self.rest_meta = instance._rest_meta
        else:
            if hasattr(self, 'Meta'):
                self.rest_meta = getattr(self.Meta.model, '_rest_meta', None)
            else:
                self.rest_meta = None
                context = kwargs.get('context', None)
                if context is not None:
                    data_mart = context.get('data_mart', None)
                    if data_mart is not None:
                        model = data_mart.entities_model
                        self.rest_meta = model._rest_meta

        super(RESTMetaSerializerMixin, self).__init__(*args, **kwargs)

    def get_serializer_to_patch(self):
        return self


class RESTMetaListSerializerPatchMixin(object):

    def get_serializer_to_patch(self):
        return self.child


class DynamicFieldsSerializerMixin(RESTMetaSerializerMixin):

    def __init__(self, *args, **kwargs):
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)
        if self.rest_meta:
            remove_fields, include_fields = self.rest_meta.exclude, self.rest_meta.include

            patch_target = self.get_serializer_to_patch()

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
                    method = getattr(self.rest_meta, method_name)
                    setattr(patch_target, method_name, types.MethodType(method, patch_target, patch_target.__class__))
                elif isinstance(field, serializers.ListField):
                    # hack for ListField.__init__ method
                    field.child.source = None
                # elif getattr(field, 'many', False): # todo: не работает когда вызывается описание поля в виде строки
                #     # hack for `many=True`
                #     field.source = None
                patch_target.fields[field_name] = field
            for field_name in remove_fields:
                patch_target.fields.pop(field_name, None)


class DynamicFieldsListSerializerMixin(RESTMetaListSerializerPatchMixin, DynamicFieldsSerializerMixin):
    pass


class DynamicCreateUpdateValidateSerializerMixin(RESTMetaSerializerMixin):

    def get_id_attrs(self):
        return self.rest_meta.lookup_fields if self.rest_meta is not None else RESTOptions.lookup_fields

    def __init__(self, *args, **kwargs):
        super(DynamicCreateUpdateValidateSerializerMixin, self).__init__(*args, **kwargs)
        if self.rest_meta:
            patch_target = self.get_serializer_to_patch()

            if self.rest_meta.validators is not None:
                patch_target.validators = self.rest_meta.validators

            for method_name in ('create', 'update', 'validate'):
                method = getattr(self.rest_meta, method_name, None)
                if method is not None:
                    setattr(patch_target, method_name, types.MethodType(getattr(method, '__func__', method),
                                                                        patch_target, patch_target.__class__))

            for method_name in self.rest_meta._fields_validators:
                method = getattr(self.rest_meta, method_name)
                setattr(patch_target, method_name, types.MethodType(method, patch_target, patch_target.__class__))


class DynamicCreateUpdateValidateListSerializerMixin(RESTMetaListSerializerPatchMixin,
                                                     DynamicCreateUpdateValidateSerializerMixin):
    pass


class BasePermissionsSerializerMixin(object):

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

    def get_permission_classes(self, data):
        return data._rest_meta.permission_classes if hasattr(data, '_rest_meta') else self.__view.permission_classes

    @cached_property
    def __request(self):
        request = self.context.get('request', None)
        assert request is not None, (
                "'%s' `.__init__()` method parameter `context` should include a `request` attribute."
                % self.__class__.__name__
        )
        return request

    @cached_property
    def __view(self):
        return self.context.get('view')

    def check_object_permissions(self, data):
        permission_classes = self.get_permission_classes(data)
        for permission in self._get_permissions(permission_classes):
            if not permission.has_object_permission(self.__request, self.__view, data):
                self.permission_denied(
                    self.__request, message=getattr(permission, 'message', None)
                )
        return permission_classes

    def check_permissions(self, data):
        permission_classes = self.get_permission_classes(data)
        for permission in self._get_permissions(permission_classes):
            if not permission.has_permission(self.__request, self.__view):
                self.permission_denied(
                    self.__request, message=getattr(permission, 'message', None)
                )
        return permission_classes


class CheckPermissionsSerializerMixin(BasePermissionsSerializerMixin):

    def __init__(self, *args, **kwargs):
        instance = args[0] if args else None
        self._permissions_cache = None if instance is not None else {}
        super(CheckPermissionsSerializerMixin, self).__init__(*args, **kwargs)

    def to_representation(self, data):
        """
        Check permissions
        """
        if self._permissions_cache is None:
            """
            Check if the request should be permitted for a given object.
            Raises an appropriate exception if the request is not permitted.
            """
            self.check_object_permissions(data)
        else:
            """
            Check if the request should be permitted for list.
            Raises an appropriate exception if the request is not permitted.
            """
            permission_classes = self._permissions_cache.get(data.__class__, None)
            if permission_classes is None:
                permission_classes = self.check_permissions(data)
                self._permissions_cache[data.__class__] = permission_classes

        return super(CheckPermissionsSerializerMixin, self).to_representation(data)


class CheckPermissionsBulkListSerializerMixin(BasePermissionsSerializerMixin):

    def validate_bulk_update(self, objects):
        """
        Hook to ensure that the bulk update should be allowed.
        """
        for obj in objects:
            self.check_object_permissions(obj)


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


class DynamicGroupByMixin(object):

    def initialize(self, request, queryset, view):
        self.request = request
        self.queryset = queryset
        self.view = view
        self.data_mart = request.GET['_data_mart']
        self.entity_model = request.GET.get(
            '_entity_model', self.data_mart.entities_model if self.data_mart is not None else queryset.model)
        self.group_by = self.entity_model._rest_meta.group_by

        method = self.entity_model._rest_meta.get_group_by
        if method is not None:
            setattr(self, 'get_group_by', types.MethodType(method, self, self.__class__))

    def get_group_by(self):
        return self.group_by
