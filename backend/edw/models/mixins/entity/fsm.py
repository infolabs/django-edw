# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from django_fsm import FSMField

from edw.models.mixins import ModelMixin


class FSMMixin(ModelMixin):
    status = FSMField(verbose_name=_("Status"), default='new', protected=True)

    @classmethod
    def get_transition_name(cls, target):
        """Return the human readable name for a given transition target"""
        return target

    def state_name(self):
        """Return the human readable name for the current transition state"""
        return self.status

