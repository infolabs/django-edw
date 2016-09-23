# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from edw.models.mixins import ModelMixin


class NotificationMixin(ModelMixin):
    """
    Dummy mixin
    """
    @property
    def customer(self):
        raise NotImplementedError