# -*- coding: utf-8 -*-
from __future__ import unicode_literals


#==============================================================================
# CustomGroupByQuerySetMixin
#==============================================================================
class CustomGroupByQuerySetMixin(object):
    '''
    Для корректной работы необходимо подключить edw/patches/sql/compiler.py
    '''

    def __init__(self, *args, **kwargs):
        # init our queryset object member variables
        self.custom_group_by = True
        super(CustomGroupByQuerySetMixin, self).__init__(*args, **kwargs)
        self.query.context['_custom_group_by'] = self.custom_group_by

    def _clone(self, *args, **kwargs):
        # Django's _clone only copies its own variables, so we need to copy ours here
        new = super(CustomGroupByQuerySetMixin, self)._clone(*args, **kwargs)
        new.custom_group_by = self.query.context['_custom_group_by'] = self.custom_group_by
        return new
