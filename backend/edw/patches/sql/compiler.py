# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models.sql.compiler import SQLCompiler


_get_group_by = SQLCompiler.get_group_by
def custom_group_by(self, select, order_by):
    if not getattr(self.query, '_custom_group_by', False) or self.query.group_by is True or not self.query.group_by:
        return _get_group_by(self, select, order_by)

    expressions = []
    if self.query.group_by is not True:
        for expr in self.query.group_by:
            if not hasattr(expr, 'as_sql'):
                expressions.append(self.query.resolve_ref(expr))
            else:
                expressions.append(expr)
    result = []
    if len(expressions):
        having_group_by = self.having.get_group_by_cols() if self.having else ()

        for expr in having_group_by:
            expressions.append(expr)

        seen = set()
        expressions = self.collapse_group_by(expressions, having_group_by)
        for expr in expressions:
            sql, params = self.compile(expr)
            if (sql, tuple(params)) not in seen:
                result.append((sql, params))
                seen.add((sql, tuple(params)))
    return result

SQLCompiler.get_group_by = custom_group_by

