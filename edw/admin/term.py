#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django_mptt_admin.admin import DjangoMpttAdmin
from django_mptt_admin.util import get_tree_from_queryset
from django.contrib.admin.utils import quote
from django.utils.translation import ugettext as _
from django.conf import settings

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple

from edw.models.term import BaseTerm


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
            #'https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.4/js/bootstrap.min.js',
            '/static/edw/js/admin/term.js',
        ]
        css = {
            'all': [
                #'https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.4/css/bootstrap.min.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.css',
                ]
        }

    def delete_model(self, request, obj):
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()


    def get_tree_data(self, qs, max_level):
        pk_attname = self.model._meta.pk.attname

        SPECIFICATION_MODES = dict((k, v) for k, v in BaseTerm.SPECIFICATION_MODES)
        SEMANTIC_RULES = dict((k, v) for k, v in BaseTerm.SEMANTIC_RULES)

        def handle_create_node(instance, node_info):
            pk = quote(getattr(instance, pk_attname))
            node_info.update(
                url=self.get_admin_url('change', (quote(pk),)),
                move_url=self.get_admin_url('move', (quote(pk),)),
                label='<div class="drag" title="%(path)s"></div><span class="term %(semantic_rule)s %(active)s%(is_characteristic)s%(is_mark)s%(is_relation)s%(has_system_flags)s"><i class="icons fa fa-exclamation-triangle has-system-flags" title="%(has_system_flags_title)s"></i><i class="icons fa fa-list is_characteristic" title="%(characteristic_title)s"></i><i class="icons fa fa-tags is_mark"  title="%(mark_title)s"></i><i class="icons fa fa-link is_relation" title="%(relation_title)s"></i><i class="icons fa fa-power-off" title="%(active_title)s"></i><span class="view_classes">%(view_classes)s</span><span class="specification_mode">%(specification_mode)s</span><img src="/static/edw/img/%(semantic_rule)s.png" alt="%(semantic_rule)s" title="%(semantic_rule)s"><div class="title" title="%(label)s">%(label)s</div></span>' % {
                    'label': node_info['label'],
                    'semantic_rule': SEMANTIC_RULES[instance.semantic_rule],
                    'specification_mode': SPECIFICATION_MODES[instance.specification_mode],
                    'active': 'on' if instance.active else 'off',
                    'is_characteristic': ' is-characteristic' if instance.attributes.is_characteristic else '',
                    'is_mark': ' is-mark' if instance.attributes.is_mark else '',
                    'is_relation': ' is-relation' if instance.attributes.is_relation else '',
                    'has_system_flags': ' has-system-flags' if instance.system_flags else '',
                    'path': instance.path,
                    'has_system_flags_title': _("System flags"),
                    'characteristic_title': _("Characteristic"),
                    'mark_title': _("Mark"),
                    'relation_title': _("Relation"),
                    'active_title': _("Active"),
                    'view_classes': ''.join(['<span class="view_class">%s</span>' % view_class for view_class in
                                     instance.view_class.split()]) if instance.view_class else ''
                }
            )

        return get_tree_from_queryset(qs, handle_create_node, max_level)

    def i18n_javascript(self, request):
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog

        return javascript_catalog(request, domain='django', packages=['django_mptt_admin', 'edw'])

