# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import fields


class ConvertNoneToStringSerializerMixin():
    """
    Mixin to convert None to empty strings.

    This must be added as the first inherited class. The property `Meta.none_to_str_fields` must
    be defined in order for this to have any effect. This only applies to representations,
    when we export our instance data, not when we acquire and validate data.

    This is how you would use it:
    class AttendanceSerializer(ConvertNoneToStringSerializerMixin, serializers.ModelSerializer):
        class Meta:
            model = Attendance
            fields = ('id', 'face_image')
            none_to_str_fields = ('face_image', )
    """
    def get_none_to_str_fields(self):
        meta = getattr(self, 'Meta', None)
        return getattr(meta, 'none_to_str_fields', [])

    def to_representation(self, instance):
        fields = self.get_none_to_str_fields()
        data = super().to_representation(instance)

        if not fields or not isinstance(data, dict):
            return data

        for field in fields:
            if field in data and data[field] is None:
                data[field] = ''
        return data


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