#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce
from celery import chain

from django.conf import settings
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:
    from django.utils.encoding import force_text

from edw.admin.entity.forms import EntitiesUpdateActiveAdminForm
from edw.tasks import update_entities_active


def update_active(modeladmin, request, queryset):
    """
    ENG: Update active for multiple entities
    RUS: Обновление активных элементов для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_RELATIONS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateActiveAdminForm(request.POST)

        if form.is_valid():
            to_set_active = form.cleaned_data['to_set_active']

            n = queryset.count()
            if n:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_entities_active.si([x.id for x in chunk], to_set_active))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateActiveAdminForm()

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Update active for multiple entities")
    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'action': 'update_active',
    }
    # Display the confirmation page
    kwargs = {}
    return TemplateResponse(request, "edw/admin/entities/actions/update_active.html",
                            context, **kwargs)


update_active.short_description = _("Modify active for selected %(verbose_name_plural)s")
