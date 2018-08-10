# -*- coding: utf-8 -*-
from django_filters.filters import (
    BaseInFilter,
    # BaseRangeFilter,
    NumberFilter,
    # DateTimeFilter,
)
from django_filters.fields import BaseCSVField

from edw.rest.filters.widgets import CSVWidget as CustomCSVWidget


class CustomCSVField(BaseCSVField):
    widget = CustomCSVWidget


class NumberInFilter(BaseInFilter, NumberFilter):
    base_field_class = CustomCSVField


# class DateTimeFromToRangeFilter(BaseRangeFilter, DateTimeFilter):
#     pass
