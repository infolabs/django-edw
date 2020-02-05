# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Count
from django.db.models.fields.related import ForeignObject
from django.db.models.options import Options
from django.db.models.sql.where import ExtraWhere
from django.db.models import DO_NOTHING
from django.db.models.sql.query import RawQuery

from edw.models.sql.datastructures import CustomJoin


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


#==============================================================================
# Join QuerySet Functionality
#==============================================================================

def join_to(queryset, subquery, table_field, subquery_field, alias, join_type, nullable):
    """
    Add a join on `subquery` to `queryset` (having table `table`).
    """
    # here you can set complex clause for join
    def extra_join_cond(where_class, alias, related_alias):
        if (alias, related_alias) == ('[sys].[columns]',
                                      '[sys].[database_permissions]'):
            where = '[sys].[columns].[column_id] = ' \
                    '[sys].[database_permissions].[minor_id]'
            children = [ExtraWhere([where], ())]
            return where_class(children)
        return None

    table = queryset.model

    foreign_object = ForeignObject(to=subquery, on_delete=DO_NOTHING, from_fields=[None], to_fields=[None],
                                   rel=None)
    foreign_object.opts = Options(table._meta)
    foreign_object.opts.model = table
    foreign_object.get_joining_columns = lambda: ((table_field, subquery_field),)
    foreign_object.get_extra_restriction = extra_join_cond

    if isinstance(subquery.query, RawQuery):
        subquery_sql, subquery_params = subquery.query.sql, subquery.query.params
    else:
        subquery_sql, subquery_params = subquery.query.sql_with_params()

    join = CustomJoin(
        subquery_sql, subquery_params, table._meta.db_table,
        alias, join_type, foreign_object, nullable)

    queryset.query.join(join)

    # hook for set alias
    join.table_alias = alias
    queryset.query.external_aliases.add(alias)

    return queryset


def inner_join_to(queryset, subquery, table_field, subquery_field, alias):
    """
    Add a INNER JOIN on `subquery` to `queryset` (having table `table`).
    """
    return join_to(queryset, subquery, table_field, subquery_field, alias, 'INNER JOIN', False)


def left_join_to(queryset, subquery, table_field, subquery_field, alias):
    """
    Add a LEFT JOIN on `subquery` to `queryset` (having table `table`).
    """
    return join_to(queryset, subquery, table_field, subquery_field, alias, 'LEFT JOIN', True)


#==============================================================================
# JoinQuerySetMixin
#==============================================================================
class JoinQuerySetMixin(object):
    """
    Добавляем функционал JOIN
    """
    def inner_join(self, subquery, table_field, subquery_field, alias):
        """
        INNER JOIN
        """
        return inner_join_to(self, subquery, table_field, subquery_field, alias)

    def left_join(self, subquery, table_field, subquery_field, alias):
        """
        LEFT JOIN
        """
        return left_join_to(self, subquery, table_field, subquery_field, alias)
