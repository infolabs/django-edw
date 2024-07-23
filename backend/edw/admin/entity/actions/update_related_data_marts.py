#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce
from celery import chain

from django.conf import settings
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:
    from django.utils.encoding import force_text

from edw.tasks import update_entities_related_data_marts
from edw.admin.entity.forms import EntitiesUpdateRelatedDataMartsAdminForm


def update_related_data_marts(modeladmin, request, queryset):
    """
    ENG: Update related data marts for multiple entities
    RUS: Обновляет связанные витрины данных для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_RELATED_DATA_MARTS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateRelatedDataMartsAdminForm(request.POST)

        if form.is_valid():
            to_set_datamarts = form.cleaned_data['to_set_datamarts']
            to_unset_datamarts = form.cleaned_data['to_unset_datamarts']

            n = queryset.count()
            if n and (to_set_datamarts or to_unset_datamarts):
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_entities_related_data_marts.si(
                        [x.id for x in chunk],
                        [j.id for j in to_set_datamarts] if to_set_datamarts else None,
                        [j.id for j in to_unset_datamarts] if to_unset_datamarts else None
                    ))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateRelatedDataMartsAdminForm(initial={'select_across': request.POST.get('select_across', '0')})

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    paginator = Paginator(queryset, modeladmin.list_per_page)

    title = _("Update related data marts for multiple entities")
    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        # 'queryset': queryset,
        'queryset': paginator.page(1),
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'action': 'update_related_data_marts',
    }
    # Display the confirmation page
    kwargs = {}
    return TemplateResponse(request, "edw/admin/entities/actions/update_related_data_marts.html",
                            context, **kwargs)


update_related_data_marts.short_description = _("Modify related data marts for selected %(verbose_name_plural)s")
