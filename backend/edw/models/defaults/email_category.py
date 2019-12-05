# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from edw.models.email_category import BaseEmailCategory


class EmailCategory(BaseEmailCategory):
    """
    ENG: Materialize many-to-many relation with email category.
    RUS: Материализованная связь многие-ко многим с почтовыми категориями.
    """
    class Meta(BaseEmailCategory.Meta):
        """
        RUS: Метаданные класса EmailCategory.
        """
        abstract = False