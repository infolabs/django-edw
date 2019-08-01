# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related.entity_file import BaseEntityFile


class EntityFile(BaseEntityFile):
    """
    ENG: Materialize many-to-many relation with files.
    RUS: Материализованная связь многие-ко многим с документами.
    """
    class Meta(BaseEntityFile.Meta):
        """
        RUS: Метаданные класса EntityFile.
        """
        abstract = False
