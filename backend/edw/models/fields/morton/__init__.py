# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.db.models import Lookup
from django.db.models.lookups import PatternLookup


def dummy_interleave_fn(*args):
    """
    :param args: Fi(*arg) --> morton code
    :return: morton code string
    RUS: Возвращает пустую строку.
    """
    return ''


def dummy_deinterleave_fn(mortoncode):
    """
    :param mortoncode: Fd(mortoncode) --> (arg1, arg2, ... , argn)
    :return: *args
    RUS: Возвращает пустой список.
    """
    return []


class BaseMortonOrder(object):

    def __init__(self, *args, **kwargs):
        """
        RUS: Конструктор объекта класса.
        """
        mortoncode = kwargs.get('mortoncode', None)
        self.interleave_fn = kwargs.get('interleave_fn', dummy_interleave_fn)
        self.deinterleave_fn= kwargs.get('deinterleave_fn', dummy_deinterleave_fn)
        self.args = args
        self._do_invalidate_args = False
        if mortoncode is None:
            self._do_invalidate_mortoncode = True
            self.mortoncode = self.interleave()
        else:
            self._do_invalidate_mortoncode = False
            self.mortoncode = mortoncode
            if not len(self.args):
                self._do_invalidate_args = True
                self.args = self.deinterleave()

    @property
    def mortoncode(self):
        """
        RUS: Возвращает переопределенный код Мортона.
        """
        return self._mortoncode

    @mortoncode.setter
    def mortoncode(self, value):
        """
        RUS: Создает код Мортона.
        """
        self._do_invalidate_args = True
        self._mortoncode = value

    def __str__(self):
        """
        RUS: Метод перегрузки оператора. Возвращает строковое представление кода Мортона.
        """
        return "{}".format(self.mortoncode)

    def __repr__(self):
        """
        RUS: Метод перегрузки оператора. Возвращает строковое представление кода Мортона.
        """
        return "{}({}: [{}])".format(self.__class__.__name__, str(self), ", ".join([str(x) for x in self.args]))

    def __len__(self):
        """
        RUS: Метод перегрузки оператора. Возвращает длину объекта.
        """
        return len(str(self))

    def __eq__(self, other):
        """
        RUS: Метод перегрузки оператора.
        Определяет поведение оператора равенства. Проверяет, является объект экземпляром класса BaseMortonOrder.
        Возвращает булевое значение.
        """
        return isinstance(other, BaseMortonOrder) and self.mortoncode == other.mortoncode

    def __ne__(self, other):
        """
        RUS: Метод перегрузки оператора.
        Определяет поведение оператора неравенства. Проверяет, не является объект экземпляром класса BaseMortonOrder.
        Возвращает булевое значение.
        """
        return not isinstance(other, BaseMortonOrder) or self.mortoncode != other.mortoncode

    def __gt__(self, other):
        """
        RUS: Метод перегрузки оператора.
        Определяет поведение оператора больше. Проверяет, не является объект экземпляром класса BaseMortonOrder.
        Возвращает булевое значение.
        """
        return not isinstance(other, BaseMortonOrder) or self.mortoncode > other.mortoncode

    def __lt__(self, other):
        """
        RUS: Метод перегрузки оператора.
        Определяет поведение оператора меньше. Проверяет, не является объект экземпляром класса BaseMortonOrder.
        Возвращает булевое значение.
        """
        return not isinstance(other, BaseMortonOrder) or self.mortoncode < other.mortoncode

    def interleave(self):
        if self._do_invalidate_mortoncode:
            self.mortoncode = self.interleave_fn(*self.args)
            self._do_invalidate_mortoncode = False
        return self.mortoncode

    def deinterleave(self):
        if self._do_invalidate_args:
            self.args = self.deinterleave_fn(self.mortoncode)
            self._do_invalidate_args = False
        return self.args


class BaseMortonField(models.Field):
    """
    RUS: Отображение полей базы данных.
    """
    description = _("BaseMortonOrder field")
    value_class = BaseMortonOrder

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        super(BaseMortonField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        """
        RUS: Возвращает текстовое название типа поля.
        """
        return 'CharField'

    def to_python(self, value):
        """
        RUS: Преобразует значения из базы данных в объект Python.
        """
        if not value:
            return None
        if isinstance(value, BaseMortonField):
            return value
        # default case is string
        return self.value_class(mortoncode=value)

    def from_db_value(self, value, expression, connection, context):
        """
        RUS: Преобразует значения из базы данных в объект Python.
        """
        return self.value_class(mortoncode=value)

    def get_prep_value(self, value):
        """
        RUS: Для преобразования типов Python в тип в базе данных.
        """
        if isinstance(value, self.value_class):
            return value.interleave()
        return str(value)

    def value_to_string(self, obj):
        """
        RUS: Преобразует значение в строку.
        Возвращает текстовый объект, представляющий значение в юникоде.
        ENG: Return a text object representing self – unicode.
        """
        value = self._get_val_from_obj(obj)
        return smart_text(value)


@BaseMortonField.register_lookup
class MortonSearchMatchedLookup(Lookup):
    """
    RUS: Поиск.
    """
    lookup_name = 'mortonsearch'

    def __init__(self, lhs, rhs):
        """
        RUS: Конструктор объекта класса.
        """
        super(MortonSearchMatchedLookup, self).__init__(lhs, rhs)

    def process_rhs(self, compiler, connection):
        """
        RUS: Возвращает кортеж, содержащий SQL и параметры для интерполяции в этот SQL для правой части запроса.
        """
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = super(MortonSearchMatchedLookup, self).process_rhs(compiler, connection)
        rhs = ''
        params = rhs_params[0]
        if params and not self.bilateral_transforms:
            rhs_params[0] = "%s%%" % connection.ops.prep_for_like_query(params)
            rhs += lhs + ' like %s'
        return rhs, rhs_params

    def as_sql(self, compiler, connection):
        """
        RUS: Для преобразования выражения запроса в SQL-запрос.
        """
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return rhs, params


@BaseMortonField.register_lookup
class MortonPreciseSearchMatchedLookup(PatternLookup):
    """
    RUS: Точный поиск.
    """
    lookup_name = 'mortonprecise'

    def __init__(self, lhs, rhs):
        super(MortonPreciseSearchMatchedLookup, self).__init__(lhs, rhs)

    def get_rhs_op(self, connection, rhs):
        return connection.operators['startswith'] % rhs

    def process_rhs(self, qn, connection):
        """
        RUS: Возвращает кортеж, содержащий SQL и параметры для интерполяции в этот SQL для правой части запроса.
        """
        rhs, params = super(MortonPreciseSearchMatchedLookup, self).process_rhs(qn, connection)
        if params and not self.bilateral_transforms:
            params[0] = "%s%%" % connection.ops.prep_for_like_query(params[0])
        return rhs, params
