# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _

from collections import OrderedDict

from edw.models.notification import NotificationAttachment
from edw.models.entity import EntityModel


class NotificationAttachmentAdmin(admin.TabularInline):
    model = NotificationAttachment
    extra = 0


class NotificationAdmin(admin.ModelAdmin):
    USER_CHOICES = (
        ('', _("Nobody")),
        (0, _("Customer")),
    )

    list_display = (
        'name',
        'transition_model',
        'transition',
        'recipient',
        'mail_template',
        'num_attachments'
    )

    inlines = (NotificationAttachmentAdmin,)

    save_as = True
    save_on_top = True

    search_fields = ('name',)

    def get_form(self, request, obj=None, **kwargs):
        kwargs.update(widgets={
            'transition_target': widgets.Select(choices=self.get_transition_choices()),
            'mail_to': widgets.Select(choices=self.get_mailto_choices()),
        })
        return super(NotificationAdmin, self).get_form(request, obj, **kwargs)

    @staticmethod
    def get_senders():
        result = {}
        Model = EntityModel.materialized
        for clazz in [Model] + Model.__subclasses__():
            result[clazz.__name__.lower()] = clazz
        return result

    def get_transition_choices(self):
        choices = {}
        for clazz in self.get_senders().values():
            status_fields = [f for f in clazz._meta.fields if f.name == 'status']
            if status_fields:
                for transition in status_fields.pop().get_all_transitions(clazz):
                    if transition.target:
                        transition_name = "{} - {}".format(
                            clazz._meta.verbose_name,
                            clazz.get_transition_name(transition.target)
                        )
                        choices[self.model.get_transition_target(clazz, transition.target)] = transition_name
        return choices.items()

    def get_mailto_choices(self):
        choices = list(self.USER_CHOICES)
        for user in get_user_model().objects.filter(is_staff=True):
            email = '{0} {1} <{2}>'.format(user.first_name, user.last_name, user.email)
            choices.append((user.id, email))
        return choices

    def transition_model(self, obj):
        sender, target = obj.transition_target.split(':')
        Model = self.get_senders()[sender]
        return Model._meta.verbose_name
    transition_model.short_description = _("Entity")

    def transition(self, obj):
        sender, target = obj.transition_target.split(':')
        Model = self.get_senders()[sender]
        return Model.get_transition_name(target)
    transition.short_description = _("Status")

    def num_attachments(self, obj):
        return obj.notificationattachment_set.count()
    num_attachments.short_description = _("Attachments")

    def recipient(self, obj):
        try:
            if obj.mail_to > 0:
                user = get_user_model().objects.get(id=obj.mail_to, is_staff=True)
                return '{0} {1} <{2}>'.format(user.first_name, user.last_name, user.email)
            else:
                return OrderedDict(self.USER_CHOICES)[obj.mail_to]
        except (get_user_model().DoesNotExist, KeyError):
            return _("Nobody")
    recipient.short_description = _("Recipient")
