# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_fsm.signals import post_transition

from edw.tasks import send_notification


def transition_event_notification(sender, instance, name, source, target, **kwargs):
    if hasattr(instance, 'send_notification'):
        send_notification.apply_async(
            kwargs={
                "entity_id": instance.id,
                "source": source,
                "target": target
            }
        )
    return

post_transition.connect(transition_event_notification)
