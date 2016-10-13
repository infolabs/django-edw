# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models.base import ModelBase


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
