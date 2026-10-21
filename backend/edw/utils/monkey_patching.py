# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types


#==============================================================================
# Patch instance method
#==============================================================================
def patch_class_method(cls, method_name, new_method):
    origin_method_name = "_origin_{}".format(method_name)
    origin_method = getattr(cls, origin_method_name, None)
    if origin_method is None:
        origin_method = getattr(cls, method_name)
        setattr(cls, origin_method_name, origin_method)
        setattr(cls, method_name, new_method)
