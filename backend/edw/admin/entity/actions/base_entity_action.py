#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce

try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:
    from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext

from celery import chain

from edw.admin.entity.forms import BaseEntityActionAdminForm


def base_entity_action(modeladmin, request, queryset, action, action_task, title, chunk_size):
    """
    Создает цепочку Celery в случае отправки запроса методом POST и валидности формы.
    Возвращает шаблон подтверждения
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = BaseEntityActionAdminForm(request.POST)

        if form.is_valid():

            n = queryset.count()
            if n:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + chunk_size]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(action_task.si([x.id for x in chunk]))

                    i += chunk_size

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = BaseEntityActionAdminForm()

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'action': action
    }
    # Display the confirmation page
    return TemplateResponse(request, "edw/admin/entities/actions/base_multiply_entities_action.html",
                            context, current_app=modeladmin.admin_site.name)
