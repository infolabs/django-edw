# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField
from post_office.models import EmailTemplate

from edw.settings import APP_LABEL

"""
Patch class `post_office.models.Email` which fixes https://github.com/ui/django-post_office/issues/116
and additionally converts HTML messages into plain text messages.
"""
from edw.models.email import Email
from edw.models.entity import EntityModel
from edw.models.customer import CustomerModel


USER_CHOICES = (
    ('', _("Nobody")),
    (0, _("Customer")),
)

TRANSITION_TARGET_PATTERN = "{}:{}"
TRANSITION_NAME_PATTERN = "{} - {}"


class Notification(models.Model):
    """
    A task executed on receiving a signal.
    """
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    transition_target = models.CharField(max_length=50, verbose_name=_("Event"))
    mail_to = models.PositiveIntegerField(verbose_name=_("Mail to"), null=True,
                                          blank=True, default=None)
    mail_template = models.ForeignKey(EmailTemplate, verbose_name=_("Template"),
                            limit_choices_to=Q(language__isnull=True) | Q(language=''))

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ('transition_target', 'mail_to')

    def get_recipient(self, entity):
        if self.mail_to is None or not hasattr(entity, 'customer'):
            return None
        if self.mail_to == 0:
            return entity.customer.email
        return CustomerModel.objects.get(pk=self.mail_to).email

    @staticmethod
    def get_senders():
        result = {}
        Model = EntityModel.materialized
        for clazz in [Model] + Model.__subclasses__():
            result[clazz.__name__.lower()] = clazz
        return result

    @staticmethod
    def get_transition_target(sender, target):
        return TRANSITION_TARGET_PATTERN.format(sender.__name__.lower(), target)

    @staticmethod
    def get_transition_choices():
        choices = {}
        for clazz in Notification().get_senders().values():
            status_fields = [f for f in clazz._meta.fields if f.name == 'status']
            if status_fields:
                for transition in status_fields.pop().get_all_transitions(clazz):
                    if transition.target:
                        transition_name = TRANSITION_NAME_PATTERN.format(
                            clazz._meta.verbose_name,
                            clazz.get_transition_name(transition.target)
                        )
                        choices[TRANSITION_TARGET_PATTERN.format(
                            clazz.__name__.lower(),
                            transition.target)
                        ] = transition_name
        return choices.items()

    @staticmethod
    def get_mailto_choices():
        choices = list(USER_CHOICES)
        for user in get_user_model().objects.filter(is_staff=True):
            email = '{0} {1} <{2}>'.format(user.first_name, user.last_name, user.email)
            choices.append((user.id, email))
        return choices


class NotificationAttachment(models.Model):
    notification = models.ForeignKey(Notification)
    attachment = FilerFileField(null=True, blank=True, related_name='email_attachment', verbose_name=_("Attachment"))

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

