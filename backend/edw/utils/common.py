# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import six

from django.conf import settings
import edw.settings as edw_settings

class obj(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)


def dict2obj(d):
    return json.loads(json.dumps(d), object_hook=obj)


class classproperty(object):
    """Like @property, but for classes, not just instances.
    Example usage:
        >>> from cms.utils.helpers import classproperty
        >>> class A(object):
        ...     @classproperty
        ...     def x(cls):
        ...         return 'x'
        ...     @property
        ...     def y(self):
        ...         return 'y'
        ...
        >>> A.x
        'x'
        >>> A().x
        'x'
        >>> A.y
        <property object at 0x2939628>
        >>> A().y
        'y'
    """
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def unicode_to_repr(value):
    # Coerce a unicode string to the correct repr return type, depending on
    # the Python version. We wrap all our `__repr__` implementations with
    # this and then use unicode throughout internally.
    if six.PY2:
        return value.encode('utf-8')
    return value


def get_from_address():
    from django.contrib.sites.models import Site
    default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL')
    sender_extra_format = getattr(edw_settings, 'SENDER_EXTRA_FORMAT')
    portal_name = Site.objects.get_current().name

    if sender_extra_format == 1:
        return f'{portal_name} <{default_from_email}>'
    return default_from_email
