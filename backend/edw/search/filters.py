# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import operator

from drf_haystack.filters import BaseHaystackFilterBackend
from drf_haystack.query import FilterQueryBuilder


class HaystackTermFilter(BaseHaystackFilterBackend):

    query_builder_class = FilterQueryBuilder
    default_operator = operator.and_


    # def build_filters(self, view, filters=None):
    #     applicable = super(HaystackTermFilter, self).build_filters(view, filters)
    #
    #     print "--------- build_filters  ----------"
    #
    #
    #     return applicable