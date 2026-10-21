# -*- coding: utf-8 -*-
"""
E1 test stub: minimal stand-in for django-bitfield (not provisioned offline).

Only the surface used by django-edw models is implemented: an integer model
field carrying named bit flags. Not part of the product.
"""
from __future__ import unicode_literals

from django.db import models


class Bit(int):
    """Minimal django-bitfield ``Bit`` compatibility object."""

    def __new__(cls, number):
        obj = int.__new__(cls, 1 << int(number))
        obj.number = int(number)
        obj.mask = obj
        return obj


class BitFieldValue(int):
    """Instance value of a bit field: integer plus named flag attributes."""

    def __new__(cls, field, value):
        obj = int.__new__(cls, int(value or 0))
        obj._field = field
        return obj

    def __getattr__(self, name):
        bit = self._field.flag_names.get(name)
        if bit is None:
            raise AttributeError(name)
        return bool(int(self) & bit)

    @property
    def mask(self):
        return int(self)


class BitFlags(object):
    """Class-level access to flag masks: ``Term.attributes.is_characteristic``."""

    def __init__(self, field):
        self._field = field

    def __getattr__(self, name):
        bit = self._field.flag_names.get(name)
        if bit is None:
            raise AttributeError(name)
        return bit


class BitFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner=None):
        if instance is None:
            return self.field.flags_namespace
        return instance.__dict__.get(self.field.attname)

    def __set__(self, instance, value):
        instance.__dict__[self.field.attname] = self.field.to_python(value)


class BitField(models.BigIntegerField):
    """Integer field with named bit flags, compatible with django-bitfield."""

    description = "Bit flags"

    def __init__(self, *args, **kwargs):
        flags = kwargs.pop('flags', None) or {}
        self.flags = flags
        self.flag_names = {}
        for bit, value in flags.items():
            name = value[0] if isinstance(value, (tuple, list)) else value
            self.flag_names[name] = 1 << int(bit)
        self.flags_namespace = BitFlags(self)
        super(BitField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        super(BitField, self).contribute_to_class(cls, name, private_only=private_only, **kwargs)
        setattr(cls, name, BitFieldDescriptor(self))

    def to_python(self, value):
        if isinstance(value, BitFieldValue):
            return value
        return BitFieldValue(self, value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return BitFieldValue(self, value)

    def get_prep_value(self, value):
        if value is None:
            return None
        return int(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return '' if value is None else str(int(value))

    def deconstruct(self):
        name, path, args, kwargs = super(BitField, self).deconstruct()
        kwargs['flags'] = self.flags
        return name, path, args, kwargs
