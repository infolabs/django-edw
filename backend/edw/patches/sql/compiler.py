# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.expressions import Ref
from django.db.models.sql.compiler import SQLCompiler


_get_group_by = SQLCompiler.get_group_by


def custom_get_group_by(self, select, order_by):
    """
    GROUP BY по явно заданному списку полей (EDW ``QuerySet.group_by``).

    Контракт компилятора Django 4.2/5.2: ``get_group_by(select, order_by)``
    возвращает список пар (sql, params). Для запросов EDW ``query.group_by``
    содержит минимальный набор выражений (строки-ссылки или выражения), и
    расширять его колонками select/order_by нельзя — иначе группировка
    перестаёт быть той, которую запросил вызывающий код.
    """
    if not getattr(self.query, '_custom_group_by', False) or self.query.group_by is True or not self.query.group_by:
        return _get_group_by(self, select, order_by)

    expressions = []
    group_by_refs = set()
    for expr in self.query.group_by:
        if not hasattr(expr, 'as_sql'):
            expr = self.query.resolve_ref(expr)
        if isinstance(expr, Ref):
            # Django 5.x группирует по источнику ссылки, а не по alias.
            if expr.refs not in group_by_refs:
                group_by_refs.add(expr.refs)
                expressions.append(expr.source)
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
            key = (sql, tuple(params))
            if key not in seen:
                result.append((sql, params))
                seen.add(key)
    return result


SQLCompiler.get_group_by = custom_get_group_by
