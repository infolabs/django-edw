#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce

from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext

from celery import chain

from edw.admin.entity.forms import EntitiesForceValidateAdminForm
from edw.tasks import entities_force_validate


def force_validate(modeladmin, request, queryset):
    """
    Save multiple entities with force validate terms
    """
    CHUNK_SIZE = getattr(settings, 'EDW_ENTITIES_FORCE_VALIDATE_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesForceValidateAdminForm(request.POST)

        if form.is_valid():
            #foo = form.cleaned_data['foo']

            n = queryset.count()
            if n:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(entities_force_validate.si([x.id for x in chunk]))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesForceValidateAdminForm()

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    title = _("Save multiple entities with force validate terms")
    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
    }
    # Display the confirmation page
    return TemplateResponse(request, "edw/admin/entities/actions/force_validate.html",
                            context, current_app=modeladmin.admin_site.name)

force_validate.short_description = _("Save with force validate terms for selected %(verbose_name_plural)s")
