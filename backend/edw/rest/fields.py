# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import fields


# Number types...

class IntegerFieldNull2Zero(fields.IntegerField):

    def to_representation(self, value):
        return 0 if value is None else super(IntegerFieldNull2Zero, self).to_representation(value)


class FloatFieldNull2Zero(fields.FloatField):

    def to_representation(self, value):
        return 0.0 if value is None else super(FloatFieldNull2Zero, self).to_representation(value)