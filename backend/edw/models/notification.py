# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField
from post_office.models import EmailTemplate

from edw.settings import APP_LABEL

from edw.models.customer import CustomerModel


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
        if self.mail_to is None or not hasattr(entity, 'customer') or entity.customer is None:
            return None
        if self.mail_to == 0:
            return entity.customer.email
        return CustomerModel.objects.get(pk=self.mail_to).email

    @staticmethod
    def get_transition_target(sender, target):
        return '{}:{}'.format(sender.__name__.lower(), target)


class NotificationAttachment(models.Model):
    notification = models.ForeignKey(Notification)
    attachment = FilerFileField(null=True, blank=True, related_name='email_attachment', verbose_name=_("Attachment"))

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

