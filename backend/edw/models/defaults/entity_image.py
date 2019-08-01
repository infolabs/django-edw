# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related.entity_image import BaseEntityImage


class EntityImage(BaseEntityImage):
    """
    ENG: Materialize many-to-many relation with images.
    RUS: Материализованная связь многие-ко многим с картинками.
    """
    class Meta(BaseEntityImage.Meta):
        """
        RUS: Метаданные класса EntityImage.
        """
        abstract = False
