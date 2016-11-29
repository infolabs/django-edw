# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types

from django.db.models.base import ModelBase
from django.utils.module_loading import import_string

from rest_framework import serializers


class RESTOptions(object):
    """
    Options class for REST models. Use this as an inner class called ``RESTMeta``::

        class MyModel(Model):
            class RESTMeta:
                exclude = ['name']
    """

    exclude = []
    include = {}

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

    # def __new__(cls, *args, **kwargs):
    #     cls.__many = kwargs.get('origin_many', kwargs.get('many', False))
    #     return super(DynamicFieldsSerializerMixin, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        instance = args[0] if args else None
        if instance is not None and hasattr(instance, '_rest_meta'):
            rest_meta = instance._rest_meta
        else:
            rest_meta = getattr(self.Meta.model, '_rest_meta', None)
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)
        if rest_meta:
            remove_fields, include_fields = (
                rest_meta.exclude, rest_meta.include)

            allowed = set(include_fields.keys()) - set(remove_fields)

            # print "+++++++++++>>>>>>>>>>>", getattr(self, 'many', False), self.__class__
            # print kwargs
            #
            # print "+++ allowed +++", allowed

            # for multiple fields in a list
            for field_name in allowed:
                field = include_fields[field_name]
            # for field_name, field in include_fields.items():
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
                self.fields[field_name] = field
            for field_name in remove_fields:
                self.fields.pop(field_name, None)

    # def _get_list_serializer_class(self):
    #     meta = getattr(self, 'Meta', None)
    #
    #     return getattr(meta, 'list_serializer_class', serializers.ListSerializer)

    # @classmethod
    # def many_init(cls, *args, **kwargs):
    #
    #     print "------------>>>>>>>>> many_init", cls
    #
    #     return super(DynamicFieldsSerializerMixin, cls).many_init(cls, *args, **kwargs)