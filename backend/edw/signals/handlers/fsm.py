# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, CHANGE
from django_fsm.signals import pre_transition, post_transition


def on_post_transition(sender, instance, name, source, target, **kwargs):
    log_fsm =  getattr(sender, 'LOG_FSM', False)
    user = getattr(instance, 'by', None)
    if log_fsm and user:
        LogEntry.objects.log_action(
            user_id         = user.pk, 
            content_type_id = ContentType.objects.get_for_model(instance).pk,
            object_id       = instance.pk,
            object_repr     = "source: %s, target: %s" % (source, target), 
            action_flag     = CHANGE
        )


def on_pre_transition(sender, instance, name, source, target, **kwargs):
    pass


#pre_transition.connect(on_pre_transition)
post_transition.connect(on_post_transition)


