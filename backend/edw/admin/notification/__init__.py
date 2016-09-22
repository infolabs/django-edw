# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.forms import widgets

from collections import OrderedDict

from edw.models.notification import NotificationAttachment


class NotificationAttachmentAdmin(admin.TabularInline):
    model = NotificationAttachment
    extra = 0


class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'transition_model_display_name',
        'transition_display_name',
        'recipient_display_name',
        'mail_template',
        'num_attachments'
    )

    search_fields = ('name',)

    inlines = (NotificationAttachmentAdmin,)

    save_as = True
    save_on_top = True

    def get_form(self, request, obj=None, **kwargs):
        kwargs.update(widgets={
            'transition_target': widgets.Select(choices=self.model.get_transition_choices()),
            'mail_to': widgets.Select(choices=self.model.get_mailto_choices()),
        })
        return super(NotificationAdmin, self).get_form(request, obj, **kwargs)

    def transition_model_display_name(self, obj):
        sender, target = obj.transition_target.split(':')
        Model = self.model.get_senders()[sender]
        return Model._meta.verbose_name
    transition_model_display_name.short_description = _("Entity")

    def transition_display_name(self, obj):
        sender, target = obj.transition_target.split(':')
        Model = self.model.get_senders()[sender]
        return Model.get_transition_name(target)
    transition_display_name.short_description = _("Event")

    def num_attachments(self, obj):
        return obj.notificationattachment_set.count()
    num_attachments.short_description = _("Attachments")

    def recipient_display_name(self, obj):
        try:
            if obj.mail_to > 0:
                user = get_user_model().objects.get(id=obj.mail_to, is_staff=True)
                return '{0} {1} <{2}>'.format(user.first_name, user.last_name, user.email)
            else:
                return OrderedDict(self.model.get_mailto_choices())[obj.mail_to]
        except (get_user_model().DoesNotExist, KeyError):
            return _("Nobody")
    recipient_display_name.short_description = _("Recipient")
