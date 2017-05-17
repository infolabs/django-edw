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

from edw.tasks import update_entities_terms, update_entities_relations, \
    update_entities_images

from edw.admin.entity.forms import EntitiesUpdateTermsAdminForm, \
        EntitiesUpdateRelationAdminForm, EntitiesUpdateImagesAdminForm


def update_terms(modeladmin, request, queryset):
    """
    Update terms for multiple entities
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
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)
                    tasks.append(update_entities_terms.si([x.id for x in chunk], to_set, to_unset))
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
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)


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
    }
    # Display the confirmation page
    return TemplateResponse(request, "edw/admin/entities/actions/update_terms.html",
                            context, current_app=modeladmin.admin_site.name)

update_terms.short_description = _("Set or unset terms for selected %(verbose_name_plural)s")


def update_relations(modeladmin, request, queryset):
    """
    Update relations for multiple entities
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_RELATIONS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateRelationAdminForm(request.POST)

        if form.is_valid():
            to_set_term = form.cleaned_data['to_set_term']
            to_set_target = form.cleaned_data['to_set_target']
            to_unset_term = form.cleaned_data['to_unset_term']
            to_unset_target = form.cleaned_data['to_unset_target']

            n = queryset.count()
            if n and ((to_set_term and to_set_target) or (to_unset_term and to_unset_target)):
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_entities_relations.si([x.id for x in chunk], to_set_term.id if to_set_term else None,
                                              to_set_target.id if to_set_target else None,
                                              to_unset_term.id if to_unset_term else None,
                                              to_unset_target.id if to_unset_target else None))
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
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)



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

update_relations.short_description = _("Set or unset relation for selected %(verbose_name_plural)s")


def update_images(modeladmin, request, queryset):
    """
    Update images for multiple entities
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_RELATIONS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateImagesAdminForm(request.POST)
        objects_name = force_unicode(opts.verbose_name)
        if form.is_valid():
            to_set = form.cleaned_data['to_set']
            to_unset = form.cleaned_data['to_unset']

            n = queryset.count()
            if n and (to_set or to_unset):
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)
                    #tasks.append(update_entities_images.si([x.id for x in chunk], to_set, to_unset))
                    update_entities_images([x.id for x in chunk], to_set, to_unset)
                    i += CHUNK_SIZE

                #chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = EntitiesUpdateImagesAdminForm()

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)


    title = _("Update images for multiple entities")
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
    return TemplateResponse(request, "edw/admin/entities/actions/update_images.html",
                            context, current_app=modeladmin.admin_site.name)

update_images.short_description = _("Set or unset images for selected %(verbose_name_plural)s")

