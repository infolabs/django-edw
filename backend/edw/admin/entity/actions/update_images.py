#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR
from functools import reduce
from celery import chain

from django.core.cache import cache
from django.core.paginator import Paginator
from django.conf import settings
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:
    from django.utils.encoding import force_text

from edw.rest.serializers.entity import EntityCommonSerializer
from edw.tasks import update_entities_images
from edw.admin.entity.forms.update_images import EntitiesUpdateImagesAdminForm


def update_images(modeladmin, request, queryset):
    """
    ENG: Update images for multiple entities
    RUS: Обновление картинок для нескольких объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_IMAGES_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateImagesAdminForm(request.POST)
        if form.is_valid():
            to_set = form.cleaned_data['to_set']
            to_set_order = form.cleaned_data['to_set_order']
            to_unset = form.cleaned_data['to_unset']

            n = queryset.count()
            if n and (to_set or to_unset):
                i = 0
                tasks = []
                languages = getattr(settings, 'LANGUAGES', ())

                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_text(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    entities_ids = []
                    for entity in chunk:
                        entities_ids.append(entity.id)

                        app_label = entity._meta.app_label.lower()

                        keys = [EntityCommonSerializer.HTML_SNIPPET_CACHE_KEY_PATTERN.format(
                            entity.id, app_label, label, entity.entity_model, 'media', language[0])
                            for label in ('summary', 'detail') for language in languages]
                        cache.delete_many(keys)

                    tasks.append(update_entities_images.si(entities_ids,
                                 [j.id for j in to_set] if to_set else None,
                                 to_set_order if to_set_order else 0,
                                 [j.id for j in to_unset] if to_unset else None))
                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateImagesAdminForm(initial={'select_across': request.POST.get('select_across', '0')})

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    paginator = Paginator(queryset, modeladmin.list_per_page)

    title = _("Update images for multiple entities")
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
        'action': 'update_images',
    }
    # Display the confirmation page
    kwargs = {}
    return TemplateResponse(request, "edw/admin/entities/actions/update_images.html",
                            context, **kwargs)


update_images.short_description = _("Modify images for selected %(verbose_name_plural)s")
