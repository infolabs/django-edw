# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related import BaseEntityFile


class EntityFile(BaseEntityFile):
    """Materialize many-to-many relation with files"""
    class Meta(BaseEntityFile.Meta):
        abstract = False
