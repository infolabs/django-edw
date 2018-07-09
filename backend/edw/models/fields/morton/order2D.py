# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

import pymorton as pm

from . import  BaseMortonOrder, BaseMortonField


class MortonOrder2D(BaseMortonOrder):

    def __init__(self, x, y, mortoncode=None):
        args = (x, y)
        super(MortonOrder2D, self).__init__(mortoncode=mortoncode,
                                            interleave_fn=pm.interleave2,
                                            deinterleave_fn=pm.deinterleave2,
                                            *args
                                            )

    @property
    def x(self):
        return self.args[0]

    @x.setter
    def x(self, value):
        self._do_invalidate_mortoncode = True
        self.args[0] = value

    @property
    def y(self):
        return self.args[1]

    @x.setter
    def y(self, value):
        self._do_invalidate_mortoncode = True
        self.args[1] = value


class MortonField2D(BaseMortonField):

    description = _("MortonOrder2D field")
    value_class = MortonOrder2D
