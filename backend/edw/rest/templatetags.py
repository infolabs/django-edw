# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property
from django.db.models.query import QuerySet
from django.http import QueryDict
from django.conf import settings

from classytags.core import Tag

from rest_framework import request
from rest_framework.request import Empty, ForcedAuthentication
from rest_framework import exceptions
from rest_framework.generics import get_object_or_404
from rest_framework.settings import api_settings
from rest_framework.renderers import JSONRenderer


def _get_count(queryset):
    """
    ENG: Determine an object count, supporting either querysets or regular lists.
    RUS: Возвращает количество объектов, поддерживающих запрос к базе данных с помощью метода .count() или len().
    """
    try:
        return queryset.count()
    except (AttributeError, TypeError):
        return len(queryset)


class Request(request.Request):

    def __init__(self, request, query_params=None, parsers=None, authenticators=None,
                     negotiator=None, parser_context=None):
        """
        Добовляет в rest_framework.request.Request возможность устанавливать query_params в конструкторе
        """
        self._query_params = query_params

        # copy from: rest_framework.request.Request.__init__
        self._request = request
        # если не устанавливать то user потеряется
        self.user = request.user
        self.parsers = parsers or ()
        self.authenticators = authenticators or ()
        self.negotiator = negotiator or self._default_negotiator()
        self.parser_context = parser_context
        self._data = Empty
        self._files = Empty
        self._full_data = Empty
        self._content_type = Empty
        self._stream = Empty

        if self.parser_context is None:
            self.parser_context = {}
        self.parser_context['request'] = self
        self.parser_context['encoding'] = request.encoding or settings.DEFAULT_CHARSET

        force_user = getattr(request, '_force_auth_user', None)
        force_token = getattr(request, '_force_auth_token', None)
        if force_user is not None or force_token is not None:
            forced_auth = ForcedAuthentication(force_user, force_token)
            self.authenticators = (forced_auth,)

    @cached_property
    def query_params(self):
        """
        ENG: More semantically correct name for request.GET.
        RUS: Параметры запроса  HTTP методов
        """
        return self._query_params if self._query_params is not None else self._request.GET

    @property
    def GET(self):
        """
        RUS: Возвращает параметры запроса
        """
        return self.query_params


class BaseRetrieveDataTag(Tag):
    """
    Основные настройки, управляющие поведением тегов
    """
    queryset = None
    serializer_class = None
    action = None

    lookup_field = 'pk'
    lookup_url_kwarg = None

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    disallow_kwargs = ['varname']

    def permission_denied(self, request, message=None):
        """
        ENG: If request is not permitted, determine what kind of exception to raise.
        RUS: Вызов исключения в случае, если неаутентифицированный запрос 
        не проходит проверку разрешений.
        """
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(detail=message)

    def get_permissions(self):
        """
        ENG: Instantiates and returns the list of permissions that this view requires.
        RUS: Возвращает список разрешений для данных представлений.
        """
        return [permission() for permission in self.permission_classes]

    def check_object_permissions(self, request, obj):
        """
        ENG: Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        RUS: Проверяет, разрешен ли запрос для данного объекта.
        Если не разрешен, создается сообщение об отказе в доступе.
        """
        permissions = [permission() for permission in obj._rest_meta.permission_classes]
        if not permissions:
            permissions = self.get_permissions()

        for permission in permissions:
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def initialize(self, origin_request, tag_kwargs):
        """
        Преобразует параметры  запросов внутренних тегов html шаблонов в запросы к REST интерфейсу
        """
        request = Request(origin_request, query_params=QueryDict('', mutable=True))
        initial_kwargs = tag_kwargs.copy()
        inner_kwargs = initial_kwargs.pop('kwargs', None)

        if inner_kwargs is not None:
            # удаляем пустые параметры
            for k, v in list(inner_kwargs.items()):
                if v == '':
                    del inner_kwargs[k]
            initial_kwargs.update(inner_kwargs)
        self.format_kwarg = initial_kwargs.pop(
            api_settings.FORMAT_SUFFIX_KWARG, None) if api_settings.FORMAT_SUFFIX_KWARG else None
        self.indent = initial_kwargs.pop('indent', None)

        for key in self.disallow_kwargs:
            initial_kwargs.pop(key, None)

        if self.action in ('retrieve', 'list'):
            # Позваляем устанавливать фильтр активности только для персонала и администраторов
            if request.user.is_active and (request.user.is_staff or request.user.is_superuser):
                request.GET.setdefault('active', True)
            else:
                request.GET['active'] = True

        request.query_params.update(initial_kwargs)
        self.initial_kwargs = initial_kwargs

        self.request = request

    def render(self, context):
        """
        Render template tag
        """
        items = self.kwargs.items()
        kwargs = dict([(key, value.resolve(context)) for key, value in items])
        kwargs.update(self.blocks)

        request = context.get('request', None)
        assert request is not None, (
            "'%s' `.render()` method parameter `context` should include a `request` attribute."
            % self.__class__.__name__
        )
        self.initialize(request, kwargs)

        return self.render_tag(context, **kwargs)

    def get_queryset(self):
        """
        ENG: Get the list of items for this Tag.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.
        RUS: Возвращает преобразованные объекты запроса Тега,
        если они являются запросами к базе данных.
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

    def get_serializer(self, *args, **kwargs):
        """
        ENG: Return the serializer instance.
        RUS: Возвращает экземпляр сериалайзера.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        """
        ENG: Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        RUS: Возвращает класс для сериалайзера.
        По умолчанию используется класс 'self.serializer_class'.
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.serializer_class

    def get_serializer_context(self):
        """
        ENG: Extra context provided to the serializer class.
        RUS: Дополнительный контекст для класса сериалайзера
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def filter_queryset(self, queryset):
        """
        ENG: Given a queryset, filter it with whichever filter backend is in use.
        RUS: Возвращает объект запроса с установленным фильтром DjangoFilterBackend.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_object(self):
        """
        ENG: Returns the object.
        RUS: Возвращает отфильтрованный объект запроса или возбуждает исключение,
        если объект не найден.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.initial_kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    @property
    def paginator(self):
        """
        ENG: The paginator instance associated with the templatetag, or `None`.
        RUS: Функция-пагинатор для управления разбитыми на страницы данными.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        ENG: Return a single page of results, or `None` if pagination is disabled.
        RUS: Возвращает страницы, содержащие запрашиваемые данные, 
        в результате обработки запроса.
        """
        if self.paginator is None:
            return None

        self._queryset_count = _get_count(queryset)
        page = self.paginator.paginate_queryset(queryset, self.request, view=self)
        self._page_len = len(page)
        return page

    def get_paginated_data(self, data):
        """
        ENG: Return a paginated style data object for the given output data.
        RUS: Определяет стиль нумерации страниц
        """
        assert self.paginator is not None

        return {
            "count": self._queryset_count,
            "is_paginated": self._page_len < self._queryset_count,
            "results": data
        }

    def to_json(self, data):
        """
        ENG: Renders the request data into JSON, using utf-8 encoding.
        RUS: Возвращает отрендеренные данные запроса JSON, используя кодировку utf-8,
        с помощью класса JSONRenderer.
        """
        return JSONRenderer().render(data, renderer_context={'indent': self.indent})
