# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.postal_zone import BasePostZone


class PostalZone(BasePostZone):
    """Materialize many-to-many relation with postzone"""
    class Meta(BasePostZone.Meta):
        abstract = False