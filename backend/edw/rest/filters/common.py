# -*- coding: utf-8 -*-
from django_filters.filters import (
    BaseInFilter,
    # BaseRangeFilter,
    NumberFilter,
    # DateTimeFilter,
)
from django_filters.fields import BaseCSVField
from django_filters.widgets import CSVWidget


class CustomCSVWidget(CSVWidget):

    def value_from_datadict(self, data, files, name):
        value = super(CSVWidget, self).value_from_datadict(data, files, name)

        if value is not None:
            try:
                return value.split(',')
            except AttributeError:
                return str(value)
        return None


class CustomCSVField(BaseCSVField):
    widget = CustomCSVWidget


class NumberInFilter(BaseInFilter, NumberFilter):
    base_field_class = CustomCSVField


# class DateTimeFromToRangeFilter(BaseRangeFilter, DateTimeFilter):
#     pass
