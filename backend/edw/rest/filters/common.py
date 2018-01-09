# -*- coding: utf-8 -*-
from django_filters.filters import (
    BaseInFilter,
    # BaseRangeFilter,
    NumberFilter,
    # DateTimeFilter,
)


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


# class DateTimeFromToRangeFilter(BaseRangeFilter, DateTimeFilter):
#     pass
