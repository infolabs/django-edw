#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django_mptt_admin.admin import DjangoMpttAdmin
from django_mptt_admin.util import get_tree_from_queryset

from edw.admin.mptt.utils import get_mptt_admin_node_template, mptt_admin_node_info_update_with_template

from django.conf import settings
from django.conf.urls import url
from django.utils.safestring import mark_safe

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple

from edw.models.term import BaseTerm, TermModel

from edw.rest.serializers.term import (
    TermListSerializer,
    TermTreeSerializer,
)

from functools import update_wrapper

from django.http import HttpResponse
from django.template.loader import render_to_string


class TermAdmin(DjangoMpttAdmin):

    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    list_filter = ('active', 'semantic_rule', 'specification_mode') #todo: Add ', ('attributes', BitFieldListFilter)', Django 1.7 support, fixes https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937

    search_fields = ['name', 'slug']

    tree_auto_open = 0

    autoescape = False


    class Media:
        js = [
            '/static/edw/js/admin/term.js',
        ]
        css = {
            'all': [
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.css',
                ]
        }

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # prepend new urls to existing urls
        return [
           url(r'^select_json/$', wrap(self.term_select_json_view), name="edw_term_select_json")
        ] + super(TermAdmin, self).get_urls()

    def delete_model(self, request, obj):
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()

    def get_tree_data(self, qs, max_level):

        SPECIFICATION_MODES = dict((k, v) for k, v in BaseTerm.SPECIFICATION_MODES)
        SEMANTIC_RULES = dict((k, v) for k, v in BaseTerm.SEMANTIC_RULES)

        def handle_create_node(instance, node_info):
            mptt_admin_node_info_update_with_template(admin_instance=self,
                                                      template=get_mptt_admin_node_template(instance),
                                                      instance=instance,
                                                      node_info=node_info,
                                                      context={
                                                                'specification_mode_name': SPECIFICATION_MODES.get(instance.specification_mode),
                                                                'semantic_rule_name': SEMANTIC_RULES.get(instance.semantic_rule),
                                                    })

        return get_tree_from_queryset(qs, handle_create_node, max_level)

    def i18n_javascript(self, request):
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog

        return javascript_catalog(request, domain='django', packages=['django_mptt_admin', 'edw'])


    def term_select_json_view(self, request):
        node_id = request.GET.get('node')
        name = request.GET.get('name')
        selected = request.GET.get('selected')

        if node_id:
            queryset = TermModel.objects.filter(parent_id=node_id)
            serializer = TermListSerializer(queryset, context={
                "request": request,
            }, many=True)

            json_data = mark_safe(render_to_string('edw/admin/term/widgets/children.json', {"nodes": serializer.data, "name": name, "selected": selected}))
        else:
            queryset = TermModel.objects.toplevel()
            serializer = TermTreeSerializer(queryset, context={
                "request": request
            }, many=True)

            json_data = mark_safe(render_to_string('edw/admin/term/widgets/tree_root.json', {"nodes": serializer.data, "name": name, "selected": selected}))


        return HttpResponse(json_data, content_type = "application/json")