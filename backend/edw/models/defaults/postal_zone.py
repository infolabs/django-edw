# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.postal_zone import BasePostZone


class PostalZone(BasePostZone):
    """
    ENG: Materialize many-to-many relation with postzone.
    RUS: Материализованная связь многие-ко многим с почтовыми зонами.
    """
    class Meta(BasePostZone.Meta):
        """
        RUS: Метаданные класса PostalZone.
        """
        abstract = False