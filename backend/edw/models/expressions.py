# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models.expressions import Func, Expression


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
