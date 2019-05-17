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

from edw.tasks import update_terms_parent as update_terms_parent_task

from edw.admin.term.forms import TermsUpdateParentAdminForm


def update_terms_parent(modeladmin, request, queryset):
    """
    Update related data marts for multiple entities
    """
    CHUNK_SIZE = getattr(settings, 'EDW_UPDATE_TERMS_PARENT_ACTION_CHUNK_SIZE', 100)

    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        form = TermsUpdateParentAdminForm(request.POST)

        if form.is_valid():
            to_set_parent_term_id = form.cleaned_data['to_set_parent_term_id']

            n = queryset.count()
            if n and to_set_parent_term_id:
                i = 0
                tasks = []
                while i < n:
                    chunk = queryset[i:i + CHUNK_SIZE]
                    for obj in chunk:
                        obj_display = force_unicode(obj)
                        modeladmin.log_change(request, obj, obj_display)

                    tasks.append(update_terms_parent_task.si(
                        [x.id for x in chunk],
                        to_set_parent_term_id.id
                    ))

                    i += CHUNK_SIZE

                chain(reduce(OR, tasks)).apply_async()

                modeladmin.message_user(request, _("Successfully proceed %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })

            # Return None to display the change list page again.
            return None

    else:
        form = TermsUpdateParentAdminForm()

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)



    title = _("Update parent for multiple terms")
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
    return TemplateResponse(request, "edw/admin/terms/actions/update_terms_parent.html",
                            context, current_app=modeladmin.admin_site.name)

update_terms_parent.short_description = _("Modify parent for selected %(verbose_name_plural)s")
