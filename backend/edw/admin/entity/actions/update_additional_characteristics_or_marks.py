#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers


from edw.admin.entity.forms import EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm


def update_additional_characteristics_or_marks(modeladmin, request, queryset):
    """
    Update additional marks for multiple entities
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_ADDITIONAL_CHARACTERISTICS_OR_MARKS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm(request.POST)
    else:
        form = EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm()

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    title = _("Update additional characteristics or marks for multiple entities")
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
    return TemplateResponse(request, "edw/admin/entities/actions/update_additional_characteristics_or_marks.html",
                            context, current_app=modeladmin.admin_site.name)


update_additional_characteristics_or_marks.short_description = \
    _("Modify additional characteristics or marks for selected %(verbose_name_plural)s")
#
