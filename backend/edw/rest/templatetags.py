# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models.query import QuerySet
from classytags.core import Tag

from rest_framework.request import Request
from rest_framework import exceptions
from rest_framework.generics import get_object_or_404
from rest_framework.settings import api_settings
from rest_framework.renderers import JSONRenderer


class BaseRetrieveDataTag(Tag):
    queryset = None
    serializer_class = None

    lookup_field = 'pk'

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    disallow_kwargs = ['varname']

    def permission_denied(self, request, message=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(detail=message)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def check_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def initialize(self, origin_request, tag_kwargs):
        request = Request(origin_request)
        initial_kwargs = tag_kwargs.copy()

        inner_kwargs = initial_kwargs.pop('kwargs', None)
        if inner_kwargs is not None:
            initial_kwargs.update(inner_kwargs)
        self.format_kwarg = initial_kwargs.pop(
            api_settings.FORMAT_SUFFIX_KWARG, None) if api_settings.FORMAT_SUFFIX_KWARG else None
        self.indent = initial_kwargs.pop('indent', None)

        for key in self.disallow_kwargs:
            initial_kwargs.pop(key, None)

        request.GET = initial_kwargs
        self.initial_kwargs = initial_kwargs

        self.request = request

    def render(self, context):
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
        Get the list of items for this Tag.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.
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
        Return the serializer instance.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.serializer_class

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_object(self):
        """
        Returns the object.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        filter_kwargs = {self.lookup_field: self.initial_kwargs[self.lookup_field]}

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def to_json(self, data):
        return JSONRenderer().render(data, renderer_context={'indent': self.indent})