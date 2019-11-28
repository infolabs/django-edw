# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bitfield import BitField
from bitfield.types import Bit
from filer.fields.file import FilerFileField
from post_office.models import EmailTemplate

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from edw.settings import APP_LABEL


class Notification(models.Model):
    """
    ENG: A task executed on receiving a signal.
    RUS: Диспетчер сигналов. Задача выполняется при получении сигнала.
    """
    MODES = {
        0: ('email', _('By Email')),
        1: ('push', _('By Push Notification')),
    }

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    transition_target = models.CharField(max_length=255, verbose_name=_("Event"))
    notify_to = models.IntegerField(verbose_name=_("Notify to"), null=True,
                                    blank=True, default=None)
    template = models.ForeignKey(EmailTemplate, verbose_name=_("Template"),
                                 limit_choices_to=Q(language__isnull=True) | Q(language=''))
    mode = BitField(flags=MODES, verbose_name=_('Mode'), default=Bit(0).mask)

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ('transition_target', 'notify_to')

    @staticmethod
    def get_transition_target(sender, target):
        """
        RUS: Возвращает уведомление вида 'отправитель: объект'.
        """
        return '{}:{}'.format(sender.__name__.lower(), target)


class NotificationAttachment(models.Model):
    """
    RUS: Приложение для уведомлений.
    Определяет поле для хранения файлов-уведомлений.
    """
    notification = models.ForeignKey(Notification)
    attachment = FilerFileField(null=True, blank=True, related_name='email_attachment', verbose_name=_("Attachment"))

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

