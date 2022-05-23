#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce

import six
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

from edw.admin.entity.forms import EntitiesUpdateTermsAdminForm


def update_terms(modeladmin, request, queryset, task, template=None):
    """
    ENG: Update terms for multiple entities
    RUS: Обновляет термины для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_TERMS_ACTION_CHUNK_SIZE', 100)
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateTermsAdminForm(request.POST)

        if form.is_valid():
            to_set = [x.id for x in form.cleaned_data['to_set']]
            to_unset = [x.id for x in form.cleaned_data['to_unset']]
            n = queryset.count()
            if n and (to_set or to_unset):
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)
                    tasks.append(task.si([x.id for x in chunk], to_set, to_unset))
                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })
            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateTermsAdminForm()

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Update terms for multiple entities")
    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'action': 'update_terms',
    }
    # Display the confirmation page
    kwargs = {} if six.PY3 else {'current_app': modeladmin.admin_site.name}
    return TemplateResponse(request, template if template is not None else "edw/admin/base_actions/update_terms.html",
                            context, **kwargs)


update_terms.short_description = _("Modify terms for selected %(verbose_name_plural)s")
