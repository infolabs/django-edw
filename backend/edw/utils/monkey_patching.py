# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types
import six


#==============================================================================
# Patch instance method
#==============================================================================
def patch_class_method(cls, method_name, new_method):
    origin_method_name = "_origin_{}".format(method_name)
    origin_method = getattr(cls, origin_method_name, None)
    if origin_method is None:
        origin_method = getattr(cls, method_name)
        if six.PY3:
            setattr(cls, origin_method_name, origin_method)
            setattr(cls, method_name, new_method)
        else:
            setattr(cls, origin_method_name, types.MethodType(origin_method, None, cls))
            setattr(cls, method_name, types.MethodType(new_method, None, cls))
