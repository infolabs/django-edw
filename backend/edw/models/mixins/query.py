# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Count


#==============================================================================
# CustomGroupByQuerySetMixin
#==============================================================================
class CustomGroupByQuerySetMixin(object):
    """
    Для корректной работы необходимо подключить edw/patches/sql/compiler.py
    """

    def __init__(self, *args, **kwargs):
        """
        ENG: init our queryset object member variables
        RUS: Конструктор класса объекта запроса.
        """
        self.custom_group_by = True
        super(CustomGroupByQuerySetMixin, self).__init__(*args, **kwargs)
        self.query.context['_custom_group_by'] = self.custom_group_by

    def _clone(self, *args, **kwargs):
        # Django's _clone only copies its own variables, so we need to copy ours here
        """
        RUS: Создает копию, переопределяя значения переменных.
        """
        new = super(CustomGroupByQuerySetMixin, self)._clone(*args, **kwargs)
        new.custom_group_by = self.query.context['_custom_group_by'] = self.custom_group_by
        return new


#==============================================================================
# CustomCountQuerySetMixin
#==============================================================================
class CustomCountQuerySetMixin(object):
    """
    В оригинале работает `return self.query.get_count(using=self.db)` довольно медленно,
    попробуем немного оптимизировать...
    """

    def count(self):
        """
        Performs a SELECT COUNT() and returns the number of records as an
        integer.
        """
        if self._result_cache is not None:
            return len(self._result_cache)

        if self.query.group_by is None:
            values = ['id']
        else:
            values = list(self.query.group_by)
            if 'id' not in set(values):
                values.insert(0, 'id')
        return self.values(*values).aggregate(__count=Count('id'))['__count']