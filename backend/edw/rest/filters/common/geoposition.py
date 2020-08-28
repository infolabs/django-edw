# -*- coding: utf-8 -*-

from django import forms

from django_filters.filters import Filter

from edw.forms.fields import BaseListField

from geoposition import GEOHASH_PRECISION, Geoposition


class GeopositionField(BaseListField):

    def __init__(self, *args, **kwargs):
        fields = (
            forms.FloatField(min_value=-90, max_value=90),
            forms.FloatField(min_value=-180, max_value=180),
            forms.IntegerField(min_value=1, max_value=GEOHASH_PRECISION, required=False)
        )
        super(GeopositionField, self).__init__(fields, min_len=2, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            # set maximum geohash precision by default
            precision = data_list[2]
            if precision is None:
                precision = GEOHASH_PRECISION
            position = Geoposition(data_list[0], data_list[1])
            return position.geohash[0:precision]
        return None


class GeopositionFilter(Filter):
    field_class = GeopositionField

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'geosearch')
        super(GeopositionFilter, self).__init__(*args, **kwargs)

