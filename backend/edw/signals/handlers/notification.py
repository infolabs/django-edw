# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django_fsm.signals import post_transition


def transition_event_notification(sender, instance, name, source, target, **kwargs):
    if hasattr(instance, 'send_notification'):
        instance.send_notification(source, target)

    return

post_transition.connect(transition_event_notification)
