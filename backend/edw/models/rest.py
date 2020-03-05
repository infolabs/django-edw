# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import types

try:
    from rest_framework_filters import MethodFilter
except ImportError:
    from edw.rest.filters.common import MethodFilter
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.fields import empty


class RESTOptions(object):
    """
    ENG: Options class for REST models. Use this as an inner class called ``RESTMeta``::

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
    RUS: Класс опций для REST модели.
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
        """
        ENG: Override defaults with options provided
        RUS: Переопределяет значение опций по умолчанию.
        """
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
        """
        ENG: Override defaults with options provided
        RUS: Возвращает объект итератора. Переписываем опции по умолчанию передоставленными данными
        """
        return ((k, v) for k, v in self.__dict__.items() if k[0] != '_')


class RESTModelBase(ModelBase):
    """
    ENG: Metaclass for REST models.
    RUS: Метакласс для REST моделей.
    """
    def __new__(cls, name, bases, attrs):
        """
        ENG: Create subclasses of Model. This:
         - adds the RESTMeta fields to the class
        RUS: Создает подклассы Модели.
        Добавляет метакласс RESTMeta поля для класса.
        Расширяет RESTMeta с базовыми классами.
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
        """
        RUS: Конструктор объектов класса.
        Переопределяет значение rest_meta.
        """
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
        """
        RUS: Определяет путь к сериалайзеру который необходимо пропатчить
        """
        return self


class RESTMetaListSerializerPatchMixin(object):

    def get_serializer_to_patch(self):
        """
        RUS: В случае списочного сериалайзера патчим `self.child`
        """
        return self.child


class DynamicFieldsSerializerMixin(RESTMetaSerializerMixin):
    """
    RUS: Миксин для динамической сериализации полей базы данных.
    Позволяет удалять и добавлять поля в сериализованное представление объекта.
    """

    def __init__(self, *args, **kwargs):
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)
        if self.rest_meta:
            remove_fields, include_fields = self.rest_meta.exclude, self.rest_meta.include

            patch_target = self.get_serializer_to_patch()

            for field_name, field in include_fields.items():
                # Конструктор сериалайзера в формате
                # ('rest_framework.serializers.CharField', <(arg1, arg2)>, <{kwarg1: val1, kwarg2: val2}>)
                if isinstance(field, (tuple, list)):
                    if isinstance(field[1], (tuple, list)):
                        if len(field) == 3:
                            field = import_string(field[0])(*field[1], **field[2])
                        else:
                            field = import_string(field[0])(*field[1])
                    else:
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

                    t_args = [method, patch_target]
                    six.PY2 and t_args.append(patch_target.__class__)
                    setattr(patch_target, method_name, types.MethodType(*t_args))

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
    """
    RUS: Миксин для динамической модификации процедуры создания, обновления и проверки в сериалайзере.
    """

    def get_id_attrs(self):
        """
        RUS: Возвращает поле для поиска с метаданными.
        """
        return self.rest_meta.lookup_fields if self.rest_meta is not None else RESTOptions.lookup_fields

    def __init__(self, *args, **kwargs):
        """
        RUS: Конструктор объектов класса.
        Добавляет методы создания, обновления, проверки по метаданным rest_meta.
        """
        super(DynamicCreateUpdateValidateSerializerMixin, self).__init__(*args, **kwargs)
        if self.rest_meta:
            patch_target = self.get_serializer_to_patch()

            if self.rest_meta.validators is not None:
                patch_target.validators = self.rest_meta.validators

            for method_name in ('create', 'update', 'validate'):
                method = getattr(self.rest_meta, method_name, None)
                if method is not None:
                    t_args = [getattr(method, '__func__', method), patch_target]
                    six.PY2 and t_args.append(patch_target.__class__)
                    setattr(patch_target, method_name, types.MethodType(*t_args))

            for method_name in self.rest_meta._fields_validators:
                method = getattr(self.rest_meta, method_name)
                setattr(patch_target, method_name, types.MethodType(method, patch_target))


class DynamicCreateUpdateValidateListSerializerMixin(RESTMetaListSerializerPatchMixin,
                                                     DynamicCreateUpdateValidateSerializerMixin):
    pass


class BasePermissionsSerializerMixin(object):
    """
    RUS: Базовы миксин для проверки разрешений в сериалайзере.
    """

    @staticmethod
    def _get_permissions(permission_classes):
        """
        ENG: Instantiates and returns the list of permissions that view requires.
        RUS: Создает и возвращает список разрешений.
        """
        # todo: Добавить в permission_class информацию о вызове
        return [permission() for permission in permission_classes]

    def permission_denied(self, request, message=None):
        """
        ENG: If request is not permitted, determine what kind of exception to raise.
        RUS: Возбуждает исключение если доступ запрещен, либо при отсутствии аутентификации.
        """
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(detail=message)

    def get_permission_classes(self, data):
        # Пытаемся получить права доступа из метаданных '_rest_meta' в противном случае из представления 'view'.
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
    """
    Миксин проверки прав доступа на уровне сериалайзера.
    """

    def __init__(self, *args, **kwargs):
        super(CheckPermissionsSerializerMixin, self).__init__(*args, **kwargs)
        # Если сериалайзер создается не под конкретный объект - инициализируем кеш
        self._permissions_cache = None if self.instance and isinstance(self.instance, models.Model) else {}

    def to_representation(self, data):
        """
        Check permissions
        RUS: Проверка разрешений. Для конкретного объекта вызываем 'check_object_permissions',
        иначе 'check_permissions'. Кешуруем результат проверки по классу переданных данных 'data'
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
    """
    RUS: Миксин разрешений доступа к массовому обновлению списка объектов сериалайзера.
    """

    def validate_bulk_update(self, objects):
        """
        ENG: Hook to ensure that the bulk update should be allowed.
        RUS: Проверка массового обновления.
        Объект запроса должен содержать атрибут.
        Проверка пользовательских разрешений.
        """
        for obj in objects:
            self.check_object_permissions(obj)


class DynamicFilterSetMixin(object):
    """
    RUS: Миксин для динамического фильтра.
    """

    def __new__(cls, data=None, queryset=None, **kwargs):
        """
        RUS: Извлекает фильтр rest_meta.
        Проверяет наличие и наименование фильтра.
        """
        it = super(DynamicFilterSetMixin, cls).__new__(cls)
        it._extra_method_filters = {}
        if data:
            data_mart = data['_data_mart']
            entity_model = data_mart.entities_model if data_mart is not None else queryset.model
            it._rest_meta = rest_meta = getattr(entity_model, '_rest_meta', None)
            if rest_meta:
                for filter_name, filter_ in rest_meta.filters.items():
                    if isinstance(filter_, (tuple, list)):
                        filter_ = import_string(filter_[0])(**filter_[1])

                    if isinstance(filter_, MethodFilter):
                        method_name = 'filter_{0}'.format(filter_name)
                        filter_.action = method_name
                        it._extra_method_filters[method_name] = getattr(rest_meta, method_name)
                    else:
                        assert filter_.name, 'Expected `name` argument in `{0}` filter constructor of {1} class'.format(
                            filter_name, filter_.__class__.__name__)

                    it.base_filters[filter_name] = filter_
        return it

    def __init__(self, *arg, **kwargs):
        """
        RUS: Конструктор класса.
        """
        for method_name, method in self._extra_method_filters.items():
            t_args = [method, self]
            six.PY2 and t_args.append(self.__class__)
            setattr(self, method_name, types.MethodType(*t_args))
        super(DynamicFilterSetMixin, self).__init__(*arg, **kwargs)


class DynamicFilterMixin(object):
    dynamic_filter_set_class = None

    def __init__(self):
        """
        RUS: Производится проверка доступа к динамическому фильтру класса.
        """
        assert self.dynamic_filter_set_class, \
            'Using DynamicFilterMixin, but `dynamic_filter_set_class` is is not defined'

    def filter_queryset(self, request, queryset, view):
        """
        RUS: Запрос к базе данных с применением фильтра.
        Добавляет фильтр к запросу к базе данных объекта rest_meta.
        """
        self.dynamic_filter_set = self.dynamic_filter_set_class(request.GET, queryset)

        queryset = self.dynamic_filter_set.qs

        # add extra `filter_queryset` from RESTMeta
        rest_meta = getattr(self.dynamic_filter_set, '_rest_meta', None)
        if rest_meta:
            filter_qs = getattr(rest_meta, 'filter_queryset', None)
            if filter_qs:
                t_args = [filter_qs, self]
                six.PY2 and t_args.append(self.__class__)
                setattr(self, '_extra_filter_queryset', types.MethodType(*t_args))
                queryset = self._extra_filter_queryset(request, queryset, view)

        return queryset


class DynamicGroupByMixin(object):

    def initialize(self, request, queryset, view):
        """
        RUS: Объект запроса, который передается методу-обработчику, является экземпляром Request инфраструктуры REST,
        а не обычным Django HttpRequest.
        Переопределяет значения объектов.
        """
        self.request = request
        self.queryset = queryset
        self.view = view
        self.data_mart = request.GET['_data_mart']
        self.entity_model = request.GET.get(
            '_entity_model', self.data_mart.entities_model if self.data_mart is not None else queryset.model)
        self.group_by = self.entity_model._rest_meta.group_by

        method = self.entity_model._rest_meta.get_group_by
        if method is not None:
            t_args = [method, self]
            six.PY2 and t_args.append(self.__class__)
            setattr(self, 'get_group_by', types.MethodType(*t_args))

    def get_group_by(self):
        """
        RUS: Получает переопределенный метод группировки данных объектов rest_meta.
        """
        return self.group_by


class UpdateOrCreateSerializerMixin(object):

    @staticmethod
    def _update_or_create_instance(model_class, id_attrs, validated_data):
        is_created = True
        for id_attr in id_attrs:
            id_value = validated_data.pop(id_attr, empty) if id_attr == 'id' else validated_data.get(id_attr, empty)
            if id_value != empty:
                try:
                    instance = model_class.objects.get(**{id_attr: id_value})
                except ObjectDoesNotExist:
                    instance = model_class.objects.create(**validated_data)
                except MultipleObjectsReturned as e:
                    raise serializers.ValidationError(e)
                else:
                    for k, v in six.iteritems(validated_data):
                        setattr(instance, k, v)
                    with transaction.atomic(using=model_class.objects.db, savepoint=False):
                        instance.save(using=model_class.objects.db)
                    is_created = False
                break
        else:
            instance = model_class.objects.create(**validated_data)

        return instance, is_created
