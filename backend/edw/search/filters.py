# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import operator

from drf_haystack.filters import BaseHaystackFilterBackend
from drf_haystack.query import FilterQueryBuilder


class HaystackTermFilter(BaseHaystackFilterBackend):

    query_builder_class = FilterQueryBuilder
    default_operator = operator.and_
