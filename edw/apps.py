# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django import get_version
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EdwConfig(AppConfig):
    name = 'edw'
    verbose_name = _("EDW")

    def ready(self):

        from edw.signals import handlers

        '''
        from django_fsm.signals import post_transition
        from jsonfield.fields import JSONField
        from rest_framework.serializers import ModelSerializer
        from shop.rest.serializers import JSONSerializerField
        from shop.models.notification import order_event_notification

        post_transition.connect(order_event_notification)
        '''



        '''
        # Monkey patches for Django-1.X
        if get_tuple_version()[:2] < (1, 9):
            from django.utils import foo_fn
            from edw.patches import foo_fn as patched_foo_fn
            foo_fn.fn = patched_foo_fn.fn
        '''

        '''
        # add JSONField to the map of customized serializers
        ModelSerializer.serializer_field_mapping[JSONField] = JSONSerializerField
        '''
        #print('Start EDW app')

'''
def get_tuple_version(version=None):
    version = version or get_version()
    return tuple(map(lambda n: int(n), version.split('.')))
'''
