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

from edw.admin.entity.forms import MakeTermsFromAdditionalCharacteristicsOrMarksAdminForm
from edw.tasks import entities_make_terms_from_additional_characteristics_or_marks


def make_terms_from_additional_characteristics_or_marks(modeladmin, request, queryset):
    """
    Make terms from additional characteristics or marks
    """
    CHUNK_SIZE = getattr(settings, 'EDW_MAKE_TERMS_FROM_ADDITIONAL_CHARACTERISTICS_OR_MARKS_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = MakeTermsFromAdditionalCharacteristicsOrMarksAdminForm(request.POST)

        if form.is_valid():
            # foo = form.cleaned_data['foo']

            n = queryset.count()
            if n:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(entities_make_terms_from_additional_characteristics_or_marks.si([x.id for x in chunk]))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = MakeTermsFromAdditionalCharacteristicsOrMarksAdminForm()

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    title = _("Make terms from additional characteristics or marks for multiple entities")
    context = {
        "title": title,
        'form': form,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'action': 'make_terms_from_additional_characteristics_or_marks'
    }
    # Display the confirmation page
    return TemplateResponse(request, "edw/admin/entities/actions/base_multiply_entities_action.html",
                            context, current_app=modeladmin.admin_site.name)


make_terms_from_additional_characteristics_or_marks.short_description = _("Make terms from additional characteristics or marks for selected %(verbose_name_plural)s")
