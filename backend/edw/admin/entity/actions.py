#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from operator import __or__ as OR

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import quote, model_ngettext

from celery import chain

from edw.tasks import update_entities_terms

from edw.admin.entity.forms import EntitiesUpdateTermsAdminForm


def update_terms(modeladmin, request, queryset):
    """
    Update terms for multiple entities
    """
    CHUNK_SIZE = 100 # todo: import from settings

    opts = modeladmin.model._meta
    app_label = opts.app_label

    def format_callback(obj):
        opts = obj._meta
        admin_url = reverse('%s:%s_%s_change'
                            % (modeladmin.admin_site.name,
                               opts.app_label,
                               opts.object_name.lower()),
                            None, (quote(obj._get_pk_val()),))
        # Display a link to the admin page.
        return mark_safe(u'%s: <a href="%s">%s</a>' %
                         (escape(capfirst(opts.verbose_name)),
                          admin_url,
                          escape(obj)))

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

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    form = EntitiesUpdateTermsAdminForm()

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