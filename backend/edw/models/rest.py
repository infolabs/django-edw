# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types

from django.db.models.base import ModelBase
from django.utils.module_loading import import_string

from rest_framework import serializers
from rest_framework import exceptions


class RESTOptions(object):
    """
    Options class for REST models. Use this as an inner class called ``RESTMeta``::

        class MyModel(Model):
            class RESTMeta:
                exclude = ['name']
    """

    exclude = []
    include = {}
    permission_classes = []

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
