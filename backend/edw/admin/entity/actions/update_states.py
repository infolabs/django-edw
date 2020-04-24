#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce

from django.utils import six
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

from edw.models.data_mart import DataMartModel
from edw.tasks import update_entities_states
from edw.admin.entity.forms import EntitiesUpdateStateAdminForm


def update_states(modeladmin, request, queryset):
    """
    ENG: Update states for multiple entities
    RUS: Обновляет состояния для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_STATES_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    try:
        terms_ids = queryset[0].terms.values_list('id', flat=True)
    except IndexError:
        entities_model = DataMartModel.get_base_entity_model()
    else:
        entities_model = DataMartModel.get_entities_model(terms_ids)

    if request.POST.get('post'):
        form = EntitiesUpdateStateAdminForm(request.POST, entities_model=entities_model)

        if form.is_valid():
            state = form.cleaned_data['state']

            n = queryset.count()
            if n and state:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_entities_states.si([x.id for x in chunk], state))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None
    else:
        form = EntitiesUpdateStateAdminForm(entities_model=entities_model)

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Update state for multiple entities")
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
    kwargs = {} if six.PY3 else {'current_app': modeladmin.admin_site.name}
    return TemplateResponse(request, "edw/admin/entities/actions/update_states.html",
                            context, **kwargs)


update_states.short_description = _("Modify state for selected %(verbose_name_plural)s")
