# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import VERSION as DJANGO_VERSION
from django.db.models.sql.datastructures import Join
from django.db.models.query import RawQuerySet


class CustomMeta:
    db_table = None


class CustomJoin(Join):
    def __init__(self, subquery, subquery_params, parent_alias, table_alias, join_type, join_field, nullable):
        self.subquery_params = subquery_params

        if DJANGO_VERSION[0] >= 3 and isinstance(join_field.related_model, RawQuerySet):
            # TODO: this is a temporary fix, check if CustomJoin works
            join_field.related_model._meta = CustomMeta

        super(CustomJoin, self).__init__(subquery, parent_alias, table_alias, join_type, join_field, nullable)

    def as_sql(self, compiler, connection):
        """
        Generates the full
        LEFT OUTER JOIN (somequery) alias ON alias.somecol = othertable.othercol, params
        clause for this join.
        """
        params = []
        sql = []
        alias_str = '' if self.table_alias == self.table_name else (' %s' % self.table_alias)
        params.extend(self.subquery_params)
        qn = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
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
        extra_cond = self.join_field.get_extra_restriction(
            compiler.query.where_class, self.table_alias, self.parent_alias)
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            extra_sql = 'AND (%s)' % extra_sql
            params.extend(extra_params)
            sql.append('%s' % extra_sql)
        sql.append(')')
        return ' '.join(sql), params

    def relabeled_clone(self, change_map):
        new_parent_alias = change_map.get(self.parent_alias, self.parent_alias)
        new_table_alias = change_map.get(self.table_alias, self.table_alias)
        return self.__class__(
            self.table_name, self.subquery_params, new_parent_alias, new_table_alias, self.join_type,
            self.join_field, self.nullable)
