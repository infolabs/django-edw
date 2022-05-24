# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from salmonella.admin import SalmonellaMixin
from salmonella.widgets import SalmonellaMultiIdWidget

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from edw.models.notification import NotificationAttachment
from edw.admin.notification.forms import NotificationForm
from edw.admin.notification.widgets import SelectMultiple


class NotificationAttachmentAdmin(admin.TabularInline):
    model = NotificationAttachment
    extra = 0


class NotificationAdmin(SalmonellaMixin, admin.ModelAdmin):

    form = NotificationForm
    readonly_fields = ('avaliable_roles',)

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    fieldsets = (
        (None, {
            'fields': ('name', 'transition', 'notify_to_roles', 'copy_to', 'template', 'mode', 'active',)
        }),
        # Скрытие служебного поля доступных ролей
        ('Hidden', {
            'classes': ('hidden',),
            'fields': ('avaliable_roles',),
        }),
    )

    list_display = (
        'name',
        'template',
        'num_attachments',
        'active'
    )

    inlines = (NotificationAttachmentAdmin,)

    save_as = True
    save_on_top = True
    search_fields = ('name',)

    def avaliable_roles(self, instance):
        """
        Скрытое поле для передачи JSON списка доступных ролей для состояний
        :param instance:
        :return: html разметку поля
        """

        avaliable = self.model.get_avalible_recipients_roles_for_notifications()

        return mark_safe(
            '<div class="avaliable-roles" data-source-field="transition" data-target-field="notify_to_roles" style="display: none;">%s</div>' % json.dumps(
                avaliable))

    avaliable_roles.short_description = ""

    def get_form(self, request, obj=None, **kwargs):
        # инициализация значений виджетов
        try:
            rel = self.model._meta.get_field("copy_to").rel
        except AttributeError:
            rel = self.model._meta.get_field("copy_to").remote_field
        kwargs.update(widgets={
            'transition': SelectMultiple(_('Transition'), False, choices=self.model.get_transition_choices()),
            'copy_to': SalmonellaMultiIdWidget(rel, admin.site)
        },
            field_classes={'avaliable_roles': 'hidden'})

        return super(NotificationAdmin, self).get_form(request, obj, **kwargs)

    def num_attachments(self, obj):
        """
        Получение количества прикрепленных файлов
        :param obj: - объект Notification
        :return: - int количество вложений
        """
        return obj.notificationattachment_set.count()
    num_attachments.short_description = _("Attachments")
