#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.contrib.admin.utils import quote, model_ngettext

from edw.admin.entity.forms import EntitiesUpdateTermsAdminForm


def update_terms(modeladmin, request, queryset):
    """
    Update terms for multiple entities
    """
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

    # def rubric_proceed(product, rubrics_set, rubrics_unset):
    #     product_rubrics = product.rubrics.all()
    #     if rubrics_set and len(rubrics_set) != 0:
    #         for rubric in rubrics_set:
    #             if not rubric in product_rubrics:
    #                 product.rubrics.add(rubric)
    #     if rubrics_unset and len(rubrics_unset) != 0:
    #         for rubric in rubrics_unset:
    #             if rubric in product_rubrics:
    #                 product.rubrics.remove(rubric)
    #     product.save()

    def update_terms(entity, to_set, to_unset):
        print ("+++ UPDATE +++", entity, to_set, to_unset)

    to_proceed = []
    for obj in queryset:
        to_proceed.append(format_callback(obj))

    if request.POST.get('post'):
        form = EntitiesUpdateTermsAdminForm(request.POST)


        if form.is_valid():
            to_set = form.cleaned_data['to_set']
            to_unset = form.cleaned_data['to_unset']
            n = queryset.count()
            if n:
                for entity in queryset:
                    obj_display = force_unicode(obj)
                    modeladmin.log_change(request, obj, obj_display)
                    update_terms(entity, to_set, to_unset)

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
        "to_proceed": [to_proceed],
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }
    # Display the confirmation page
    return TemplateResponse(request, "edw/admin/entities/actions/update_terms.html",
                            context, current_app=modeladmin.admin_site.name)

update_terms.short_description = _("Set or unset terms for selected %(verbose_name_plural)s")