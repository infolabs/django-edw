# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models.expressions import Func, F, Expression


# SQLite & MYSQL function to force a date time subtraction to come out correctly.
# This just returns the expression on every other database backend.
class ToSeconds(Func):
    function = ''
    template = "%(expressions)s"

    def __init__(self, expression, **extra):
        self.__expression = expression
        super(ToSeconds, self).__init__(expression, **extra)

    def as_sqlite(self, compiler, connection):
        self.function = 'julianday'
        # Convert julian day to seconds as used by Django DurationField
        self.template = "coalesce(%(function)s(%(expressions)s),julianday('now'))*24*60*60"
        return super(ToSeconds, self).as_sql(compiler, connection)

    def as_mysql(self, compiler, connection):
        self.function = 'TO_SECONDS'
        # Return the date or datetime argument converted to seconds since Year 0
        self.template = '%(function)s(%(expressions)s)'
        return super(ToSeconds, self).as_sql(compiler, connection)


class Sin(Func):
    function = 'SIN'


class Cos(Func):
    function = 'COS'


class Acos(Func):
    function = 'ACOS'


class Radians(Func):
    function = 'RADIANS'


class CharLength(Func):
    function = 'CHAR_LENGTH'


class Position(Func):
    function = 'POSITION'
    arg_joiner = ' IN '


class SubstrJoiner(str):
    def join(self, s):
        return str(s[0]) + " FROM " + str(s[1]) + " FOR " + str(s[2])


class Substring(Func):
    function = 'SUBSTRING'
    arg_joiner = SubstrJoiner()


class Cast(Func):
    function = 'CAST'
    arg_joiner = ' AS '


class Decimal(Func):
    function = 'Decimal'


# =========================================================================================================
# Add Django 1.11 features support
# Referencing columns from the outer queryset
# Subquery() expressions
# =========================================================================================================
try:
    from django.db.models.expressions import (
        ResolvedOuterRef,
        OuterRef,
        Subquery
    )
except ImportError:

    class ResolvedOuterRef(F):
        """
        An object that contains a reference to an outer query.
        In this case, the reference to the outer query has been resolved because
        the inner query has been used as a subquery.
        """
        def as_sql(self, *args, **kwargs):
            raise ValueError(
                'This queryset contains a reference to an outer query and may '
                'only be used in a subquery.'
            )

        def _prepare(self, output_field=None):
            return self

        def relabeled_clone(self, relabels):
            return self


    class OuterRef(F):
        def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
            if isinstance(self.name, self.__class__):
                return self.name
            return ResolvedOuterRef(self.name)

        def _prepare(self, output_field=None):
            return self


    class Subquery(Expression):
        """
        An explicit subquery. It may contain OuterRef() references to the outer
        query which will be resolved when it is applied to that query.
        """
        template = '(%(subquery)s)'

        def __init__(self, queryset, output_field=None, **extra):
            self.queryset = queryset
            self.extra = extra
            super(Subquery, self).__init__(output_field)

        def _resolve_output_field(self):
            if len(self.queryset.query.select) == 1:
                return self.queryset.query.select[0].field
            return super(Subquery, self)._resolve_output_field()

        def copy(self):
            clone = super(Subquery, self).copy()
            clone.queryset = clone.queryset.all()
            return clone

        def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
            clone = self.copy()
            clone.is_summary = summarize
            clone.queryset.query.bump_prefix(query)

            # Need to recursively resolve these.
            def resolve_all(child):
                if hasattr(child, 'children'):
                    [resolve_all(_child) for _child in child.children]
                if hasattr(child, 'rhs'):
                    child.rhs = resolve(child.rhs)

            def resolve(child):
                if hasattr(child, 'resolve_expression'):
                    resolved = child.resolve_expression(
                        query=query, allow_joins=allow_joins, reuse=reuse,
                        summarize=summarize, for_save=for_save,
                    )
                    # Add table alias to the parent query's aliases to prevent
                    # quoting.
                    if hasattr(resolved, 'alias') and resolved.alias != resolved.target.model._meta.db_table:
                        clone.queryset.query.external_aliases.add(resolved.alias)
                    return resolved
                return child

            resolve_all(clone.queryset.query.where)

            for key, value in clone.queryset.query.annotations.items():
                if isinstance(value, Subquery):
                    clone.queryset.query.annotations[key] = resolve(value)

            return clone

        def get_source_expressions(self):
            return [
                x for x in [
                    getattr(expr, 'lhs', None)
                    for expr in self.queryset.query.where.children
                ] if x
            ]

        def relabeled_clone(self, change_map):
            clone = self.copy()
            clone.queryset.query = clone.queryset.query.relabeled_clone(change_map)
            clone.queryset.query.external_aliases.update(
                alias for alias in change_map.values()
                if alias not in clone.queryset.query.alias_map
            )
            return clone

        def as_sql(self, compiler, connection, template=None, **extra_context):
            connection.ops.check_expression_support(self)

            # template_params = {**self.extra, **extra_context}
            template_params = self.extra.copy()
            template_params.update(extra_context)

            template_params['subquery'], sql_params = self.queryset.query.get_compiler(connection=connection).as_sql()

            template = template or template_params.get('template', self.template)
            sql = template % template_params
            return sql, sql_params

        def _prepare(self, output_field):
            # This method will only be called if this instance is the "rhs" in an
            # expression: the wrapping () must be removed (as the expression that
            # contains this will provide them). SQLite evaluates ((subquery))
            # differently than the other databases.
            if self.template == '(%(subquery)s)':
                clone = self.copy()
                clone.template = '%(subquery)s'
                return clone
            return self
