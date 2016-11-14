# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related import BaseDataMartImage


class DataMartImage(BaseDataMartImage):
    """Materialize many-to-many relation with images"""
    class Meta(BaseDataMartImage.Meta):
        abstract = False
