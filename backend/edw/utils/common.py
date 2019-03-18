# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json


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
