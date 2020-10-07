# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import fields


# Number types...

class IntegerFieldNull2Zero(fields.IntegerField):
    """
    Класс поля с целочисленными данными
    """

    def to_representation(self, value):
        """
         Возвращает целочисленный тип данных, преобразованный в сериализуемый
        """
        return 0 if value is None else super(IntegerFieldNull2Zero, self).to_representation(value)


class FloatFieldNull2Zero(fields.FloatField):
    """
    Класс поля с числовыми данными с плавающей точкой
    """

    def to_representation(self, value):
        """
        Возвращает числа с плавающей точкой, преобразованные в сериализуемые
        """
        return 0.0 if value is None else super(FloatFieldNull2Zero, self).to_representation(value)


class IntegerFieldZero2Null(fields.IntegerField):
    """
    Класс поля с целочисленными данными
    """

    def to_representation(self, value):
        """
         Возвращает целое число если значение не равно 0, иначе Null
        """
        return None if value == 0 else super(IntegerFieldZero2Null, self).to_representation(value)


class FloatFieldZero2Null(fields.FloatField):
    """
    Класс поля с целочисленными данными
    """

    def to_representation(self, value):
        """
         Возвращает целое число если значение не равно 0, иначе Null
        """
        return None if value == 0.0 else super(FloatFieldZero2Null, self).to_representation(value)