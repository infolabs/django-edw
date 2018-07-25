# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related.entity_image import BaseEntityImage


class EntityImage(BaseEntityImage):
    """Materialize many-to-many relation with images"""
    class Meta(BaseEntityImage.Meta):
        abstract = False
