#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import update_wrapper

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf.urls import url
from django.utils.safestring import mark_safe

from rest_framework.serializers import BooleanField

from edw.models.term import BaseTerm, TermModel
from edw.rest.viewsets import remove_empty_params_from_request
from edw.rest.serializers.term import TermSummarySerializer
from edw.admin.term.serializers import WidgetTermTreeSerializer
from edw.admin.term.actions import update_terms_parent
from edw.admin.mptt.tree import EdwMpttAdmin


class TermAdmin(EdwMpttAdmin):
    """
    Административная форма добавления/редактирования терминов
    """
    # todo: Add ', ('attributes', BitFieldListFilter)',
    # Django 1.7 support, fixes
    # https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937
    list_filter = ('active', 'semantic_rule', 'specification_mode')

    list_display = ['name', 'slug', 'parent', 'semantic_rule', 'specification_mode', 'view_class', 'active']

    fieldsets = (
        ("", {
            'fields': ('parent', 'name', 'slug', 'path', 'attributes', 'semantic_rule', 'specification_mode',
                       'view_class', 'active', 'system_flags', 'description'),
        }),
    )

    search_fields = ['name', 'slug', 'id', 'parent__slug', 'parent__name', 'view_class']

    tree_auto_open = 0

    actions = [update_terms_parent]

    change_tree_template = 'edw/admin/term/change_list.html'

    class Media:
        """
        Подключаемые JavaScript, CSS-стили
        """
        js = [
            '/static/edw/js/admin/term.js',
        ]
        css = {
            'all': [
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.min.css',
            ]
        }

    def get_urls(self):
        """
        возвращает URL, которые используются для ModelAdmin в URLCONF
        """
        def wrap(view, cacheable=False):
            """
            Функция-обертка для проверки прав и отключения кэширования
            """
            def wrapper(*args, **kwargs):
                """
                Возвращает Функцию-обертку для проверки прав и отключения кэширования
                """
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # prepend new urls to existing urls
        return [
            url(r'^select_json/$', wrap(self.term_select_json_view), name="edw_term_select_json")
        ] + super(TermAdmin, self).get_urls()

    @remove_empty_params_from_request()
    def term_select_json_view(self, request):
        """
        Предоставляет возможность выбрать (отметить) термин при соответствии указанных параметров
        """
        node_id = request.GET.get('node')
        name = request.GET.get('name')
        node_template = request.GET.get('node_template')
        tagging_restriction = BooleanField().to_internal_value(request.GET.get('tagging_restriction', False))

        context = {
            "request": request
        }

        if node_id:
            queryset = TermModel.objects.filter(parent_id=node_id)
            if tagging_restriction:
                queryset = queryset.exclude(system_flags=BaseTerm.system_flags.external_tagging_restriction)
            if BooleanField().to_internal_value(request.GET.get('active_only', False)):
                queryset = queryset.active()
            serializer = TermSummarySerializer(queryset, context=context, many=True)
            template = 'edw/admin/term/widgets/tree/children.json'
        else:
            queryset = TermModel.objects.toplevel()
            if tagging_restriction:
                queryset = queryset.exclude(system_flags=BaseTerm.system_flags.external_tagging_restriction)
            serializer = WidgetTermTreeSerializer(queryset, context=context, many=True)
            template = 'edw/admin/term/widgets/tree/toplevel.json'

        return HttpResponse(mark_safe(render_to_string(template, {
            "nodes": serializer.data,
            "name": name,
            "node_template": node_template,
            "tagging_restriction": tagging_restriction
        })), content_type="application/json")
