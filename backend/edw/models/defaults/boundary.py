# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.boundary import BaseBoundary


class Boundary(BaseBoundary):
    """
    ENG: Materialize many-to-many relation with boundary.
    RUS: Материализованная связь многие-ко многим с границами региона.
    """
    class Meta(BaseBoundary.Meta):
        """
        RUS: Метаданные класса Boundary.
        """
        abstract = False