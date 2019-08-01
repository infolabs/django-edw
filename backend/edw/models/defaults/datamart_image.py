# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related.data_mart_image import BaseDataMartImage


class DataMartImage(BaseDataMartImage):
    """
    ENG: Materialize many-to-many relation with images.
    RUS: Материализованная связь многие-ко многим с картинками.
    """
    class Meta(BaseDataMartImage.Meta):
        abstract = False
