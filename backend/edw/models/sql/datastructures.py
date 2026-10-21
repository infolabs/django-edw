# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.query import RawQuerySet
from django.db.models.sql.datastructures import Join


class CustomMeta:
    db_table = None


class CustomJoin(Join):
    """
    JOIN по произвольному подзапросу (SQL-строка + параметры).

    Контракт компилятора Django 4.2/5.2 требует от элемента alias_map:
    ``table_name``, ``table_alias``, ``parent_alias``, ``join_type``,
    ``join_field``, ``nullable``, ``filtered_relation``, ``as_sql()`` и
    ``relabeled_clone()``. Для «сырого» подзапроса Django не может вывести
    колонки связи из ``join_field.get_joining_fields()``, поэтому пары колонок
    задаются явно (``join_cols``), а дополнительные условия JOIN — через
    ``join_field.get_extra_restriction(alias, related_alias)`` (сигнатура
    Django 4.0+).
    """

    def __init__(self, subquery, subquery_params, parent_alias, table_alias, join_type,
                 join_field, nullable, join_cols=None):
        # Атрибуты Join выставляются вручную: super().__init__ выводит join_cols
        # из join_field.get_joining_fields(), что для подзапроса невозможно
        # (from_fields/to_fields у такого join_field не заданы).
        self.table_name = subquery
        self.subquery_params = subquery_params
        self.parent_alias = parent_alias
        self.table_alias = table_alias
        self.join_type = join_type
        self.join_field = join_field
        self.nullable = nullable
        self.filtered_relation = None
        self.join_fields = None
        if join_cols is None:
            join_cols = join_field.get_joining_columns()
        self.join_cols = tuple(join_cols)

        if isinstance(join_field.related_model, RawQuerySet):
            # TODO: this is a temporary fix, check if CustomJoin works
            join_field.related_model._meta = CustomMeta

    def as_sql(self, compiler, connection):
        """
        Generates the full
        LEFT OUTER JOIN (somequery) alias ON alias.somecol = othertable.othercol, params
        clause for this join.
        """
        params = []
        sql = []
        params.extend(self.subquery_params)
        qn = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
        alias_str = '' if self.table_alias == self.table_name else (' %s' % qn(self.table_alias))
        sql.append('%s (%s)%s ON (' % (self.join_type, self.table_name, alias_str))
        for index, (lhs_col, rhs_col) in enumerate(self.join_cols):
            if index != 0:
                sql.append(' AND ')
            sql.append('%s.%s = %s.%s' % (
                qn(self.parent_alias),
                qn2(lhs_col),
                qn(self.table_alias),
                qn2(rhs_col),
            ))
        # Контракт Django 4.0+: get_extra_restriction(alias, related_alias).
        extra_cond = self.join_field.get_extra_restriction(self.table_alias, self.parent_alias)
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            sql.append(' AND (%s)' % extra_sql)
            params.extend(extra_params)
        sql.append(')')
        return ' '.join(sql), params

    def relabeled_clone(self, change_map):
        new_parent_alias = change_map.get(self.parent_alias, self.parent_alias)
        new_table_alias = change_map.get(self.table_alias, self.table_alias)
        return self.__class__(
            self.table_name, self.subquery_params, new_parent_alias, new_table_alias, self.join_type,
            self.join_field, self.nullable, self.join_cols)
