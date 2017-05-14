# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django import get_version
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EdwConfig(AppConfig):
    name = 'edw'
    verbose_name = _("EDW")

    def ready(self):
        # Monkey patches
        from edw import patches

        # Signals handlers
        from edw.signals import handlers

        '''
        # Monkey patches for Django-1.X
        if get_tuple_version()[:2] < (1, 9):
            from django.utils import foo_fn
            from edw.patches.django_lt_1_9 import foo_fn as patched_foo_fn
            foo_fn.fn = patched_foo_fn.fn
        '''


'''
def get_tuple_version(version=None):
    version = version or get_version()
    return tuple(map(lambda n: int(n), version.split('.')))
'''
