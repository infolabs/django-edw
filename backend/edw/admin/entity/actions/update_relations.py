#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce

from django.conf import settings
try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:
    from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext

from celery import chain

from edw.tasks import update_entities_relations

from edw.admin.entity.forms import EntitiesUpdateRelationAdminForm


def update_relations(modeladmin, request, queryset):
    """
    ENG: Update relations for multiple entities
    RUS: Обновляет отношения для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_RELATIONS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateRelationAdminForm(request.POST)

        if form.is_valid():
            to_set_term = form.cleaned_data['to_set_term']
            to_set_targets = form.cleaned_data['to_set_targets']
            to_unset_term = form.cleaned_data['to_unset_term']
            to_unset_targets = form.cleaned_data['to_unset_targets']

            n = queryset.count()
            if n and ((to_set_term and to_set_targets) or (to_unset_term and to_unset_targets)):
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_entities_relations.si([x.id for x in chunk],
                                              to_set_term.id if to_set_term else None,
                                              [x.id for x in to_set_targets],
                                              to_unset_term.id if to_unset_term else None,
                                              [x.id for x in to_unset_targets]))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateRelationAdminForm()

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Update relations for multiple entities")
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
    return TemplateResponse(request, "edw/admin/entities/actions/update_relations.html",
                            context, current_app=modeladmin.admin_site.name)

update_relations.short_description = _("Modify relation for selected %(verbose_name_plural)s")
