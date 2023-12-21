# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import BigIntegerField
from django.db.models.expressions import Func, F, Expression


class ToSeconds(Func):
    """
    ENG: SQLite & MYSQL function to force a date time subtraction to come out correctly.
    This just returns the expression on every other database backend.
    RUS: Выполняет корректное отображение даты для запросов к базам данных SQLite и MySQL.
    """
    function = ''
    template = "%(expressions)s"

    def __init__(self, expression, **extra):
        extra.setdefault('output_field', BigIntegerField())
        self.__expression = expression
        super(ToSeconds, self).__init__(expression, **extra)

    def as_sqlite(self, compiler, connection):
        """
        ENG: Convert julian day to seconds as used by Django DurationField.
        RUS: Конвертирует юлианский день в секунды и возвращает дату, преобразованную 
        для выполнения запроса к базе данных SQLite.
        """
        self.function = 'julianday'
        self.template = "coalesce(%(function)s(%(expressions)s),julianday('now'))*24*60*60"
        return super(ToSeconds, self).as_sql(compiler, connection)

    def as_mysql(self, compiler, connection):
        """
        ENG: Return the date or datetime argument converted to seconds since Year 0.
        RUS: Возвращает аргумент date или datetime, преобразованный в секунды с года 0 
        для выполнения запроса к базе данных MySQL.
        """
        self.function = 'TO_SECONDS'
        self.template = '%(function)s(%(expressions)s)'
        return super(ToSeconds, self).as_sql(compiler, connection)

    def as_postgresql(self, compiler, connection):
        self.function = 'epoch'
        self.template = 'EXTRACT(%(function)s FROM %(expressions)s)'
        return super(ToSeconds, self).as_sql(compiler, connection)


class Sin(Func):
    """
    ENG: Return the sine of a number.
    RUS: Возвращает синус числа.
    """
    function = 'SIN'


class Cos(Func):
    """
    ENG: Return the cosine of a number.
    RUS: Возвращает косинус числа.
    """
    function = 'COS'


class Acos(Func):
    """
    ENG: Return the arc cosine of a number.
    RUS: Возвращает арккосинус числа.
    """
    function = 'ACOS'


class Ln(Func):
    """
    ENG: Return the Natural Logarithm of a Number.
    RUS: Возвращает натуральный логарифм числа.
    """
    function = 'LN'


class Power(Func):
    """
    ENG: Returns the value of a number raised to the power of another number.
    RUS: Возвращает число возведенное в степень.
    """
    function = 'POWER'


class Radians(Func):
    """
    ENG: Converts a value from degrees to radians.
    RUS: Преобразовывает значение из градусов в радианы.
    """
    function = 'RADIANS'


class CharLength(Func):
    """
    ENG: Return the length (how many characters are there) of a given string.
    RUS: Возвращает длину (количество символов) указанной строки.
    """
    function = 'CHAR_LENGTH'


class Position(Func):
    """
    ENG: Return the position of the first occurrence of a substring in a string.
    RUS: Возвращает местоположение подстроки в строке.
    """
    function = 'POSITION'
    arg_joiner = ' IN '


class SubstrJoiner(str):

    def join(self, s):
        """
        RUS: Извлекает подстроку из строки и соединяет ее с текстом.
        """
        return str(s[0]) + " FROM " + str(s[1]) + " FOR " + str(s[2])


class Substring(Func):
    """
    ENG: Extracts a substring from a string (starting at any position).
    RUS: Извлекает подстроку из строки (начиная с любой позиции).
    """
    function = 'SUBSTRING'
    arg_joiner = SubstrJoiner()


class Cast(Func):
    """
    ENG: Converts a value (of any type) into the specified datatype.
    RUS: Преобразует значение (любого типа) в указанный тип данных.
    """
    function = 'CAST'
    arg_joiner = ' AS '


class Decimal(Func):
    """
    ENG: Function for working with decimal data types with high accuracy.
    RUS: Функция для  работы с десятичным типом данных с высокой точностью.
    Определяет число знаков после запятой.
    """
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
        ENG: An object that contains a reference to an outer query.
        In this case, the reference to the outer query has been resolved because
        the inner query has been used as a subquery.
        RUS: Объект, содержащий ссылку на внешний запрос. В этом случае ссылка на внешний запрос была разрешена,
        так как внутренний запрос был использован в качестве подзапроса.
        """
        def as_sql(self, *args, **kwargs):
            """
            RUS: Функция для SQL-запроса.
            Возбуждает исключение, когда в функцию передан аргумент с неподдерживаемым значением
            (не может вызываться непосредственно из данной функции).
            """
            raise ValueError(
                'This queryset contains a reference to an outer query and may '
                'only be used in a subquery.'
            )

        def _prepare(self, output_field=None):
            """
            RUS: Подготовительная функция. Возвращает тоже значение.
            """
            return self

        def relabeled_clone(self, relabels):
            """
            ENG: Returns a clone (copy) of self, with any column aliases relabeled. 
            Column aliases are renamed when subqueries are created.
            RUS: Возвращает клон (копию) self с любыми названиями столбцов. 
            Названия столбцов переименовываются при создании подзапросов.
            """
            return self


    class OuterRef(F):
        """
        ENG: Use when a queryset in a Subquery needs to refer to a field from the outer query.
        It acts like an F expression except that the check to see if it refers
        to a valid field isn’t made until the outer queryset is resolved.
        RUS: Ссылается на поле из внешнего запроса при запросе к базе данных.
        Проверка ссылки на допустимое поле не выполняется до разрешения внешнего набора запросов.
        Экземпляры данного класса могут использоваться вместе с вложенными экземплярами подзапроса
        для ссылки на содержащий набор запросов, который не является непосредственным родителем.
        """
        def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
            """
            ENG: Provides the chance to do any pre-processing or validation of the expression before
            it’s added to the query.
            RUS: Предоставляет возможность выполнить любую предварительную обработку или проверку
            выражения перед его добавлением в запрос.
            """
            if isinstance(self.name, self.__class__):
                return self.name
            return ResolvedOuterRef(self.name)

        def _prepare(self, output_field=None):
            """
            RUS: Подготовительная функция. Возвращает тоже значение.
            """
            return self


    class Subquery(Expression):
        """
        ENG: An explicit subquery. It may contain OuterRef() references to the outer
        query which will be resolved when it is applied to that query.
        RUS: Класс подзапроса. Может содержать ссылки OuterRef() на внешний запрос, который будет
        разрешен при его применении к этому запросу.
        """
        template = '(%(subquery)s)'

        def __init__(self, queryset, output_field=None, **extra):
            """
            ENG: Class constructor automatically called when objects are created.
            RUS: Конструктор класса, автоматически вызывается при создании объектов.
            """
            self.queryset = queryset
            self.extra = extra
            super(Subquery, self).__init__(output_field)

        def _resolve_output_field(self):
            """
            RUS: Возвращает все непустые запросы или возвращает подзапросы одинакового типа.
            """
            if len(self.queryset.query.select) == 1:
                return self.queryset.query.select[0].field
            return super(Subquery, self)._resolve_output_field()

        def copy(self):
            """
            RUS: Возвращает копию запроса.
            """
            clone = super(Subquery, self).copy()
            clone.queryset = clone.queryset.all()
            return clone

        def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
            """
            ENG: Provides the chance to do any pre-processing or validation of the expression
            before it’s added to the query.
            RUS: Предоставляет возможность выполнить любую предварительную обработку или проверку
            выражения перед его добавлением в запрос.
            Копия возвращается с данными, приведенными к одному типу.
            """
            clone = self.copy()
            clone.is_summary = summarize
            clone.queryset.query.bump_prefix(query)

            # Need to recursively resolve these.
            def resolve_all(child):
                """
                RUS: Осуществляет предварительную проверку дочерних экземпляров модели.
                """
                if hasattr(child, 'children'):
                    [resolve_all(_child) for _child in child.children]
                if hasattr(child, 'rhs'):
                    child.rhs = resolve(child.rhs)

            def resolve(child):
                """
                RUS: Осуществляет запрос к базе данных, если они являются одного типа.
                Создает копию запроса, если объекты не являются идентичными с объектами из базы данных
                """
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
            """
            ENG: Takes a list of expressions and returns an ordered list of inner expressions.
            RUS: Сохраняет список выражений и возвращает их в упорядоченном виде.
            """
            return [
                x for x in [
                    getattr(expr, 'lhs', None)
                    for expr in self.queryset.query.where.children
                ] if x
            ]

        def relabeled_clone(self, change_map):
            """
            ENG: Returns a clone (copy) of self, with any column aliases relabeled.
            Column aliases are renamed when subqueries are created.
            RUS: Возвращает клон (копию) запроса с любыми псевдонимами полей.
            Старые псевдонимы полей переименовываются в новые.
            """
            clone = self.copy()
            clone.queryset.query = clone.queryset.query.relabeled_clone(change_map)
            clone.queryset.query.external_aliases.update(
                alias for alias in change_map.values()
                if alias not in clone.queryset.query.alias_map
            )
            return clone

        def as_sql(self, compiler, connection, template=None, **extra_context):
            """
            ENG: Generates the SQL for the database function, support custom keyword argument.
            RUS: Создает SQL-запрос к базе данных c пользовательскими аргументами ключевых слов.
            """
            connection.ops.check_expression_support(self)

            # template_params = {**self.extra, **extra_context}
            template_params = self.extra.copy()
            template_params.update(extra_context)

            template_params['subquery'], sql_params = self.queryset.query.get_compiler(connection=connection).as_sql()

            template = template or template_params.get('template', self.template)
            sql = template % template_params
            return sql, sql_params

        def _prepare(self, output_field):
            """
            RUS: Вызывается, если rhs экземпляра содержится в выражении.
            """
            # This method will only be called if this instance is the "rhs" in an
            # expression: the wrapping () must be removed (as the expression that
            # contains this will provide them). SQLite evaluates ((subquery))
            # differently than the other databases.
            if self.template == '(%(subquery)s)':
                clone = self.copy()
                clone.template = '%(subquery)s'
                return clone
            return self
