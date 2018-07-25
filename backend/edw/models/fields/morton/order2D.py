# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

import pymorton as pm

from . import  BaseMortonOrder, BaseMortonField



def interleave_fn(*args):
    """
    :param args: Fi(*arg) --> morton code
    :return: morton code string
    """
    return str(pm.interleave2(*args))


def deinterleave_fn(mortoncode):
    """
    :param mortoncode: Fd(mortoncode) --> (arg1, arg2, ... , argn)
    :return: *args
    """
    try:
        value = pm.deinterleave2(int(mortoncode))
    except:
        return []
    else:
        return value


class MortonOrder2D(BaseMortonOrder):

    def __init__(self, *args, **kwargs):
        kwargs['interleave_fn'] = interleave_fn
        kwargs['deinterleave_fn'] = deinterleave_fn

        super(MortonOrder2D, self).__init__(*args, **kwargs)

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
