#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import SerializerMethodField

from edw.rest.serializers.term import TermTreeSerializer


class WidgetTermTreeSerializer(TermTreeSerializer):
    """
    Widget Term Tree Serializer
    """
    tagging_restriction = SerializerMethodField()

    class Meta(TermTreeSerializer.Meta):
        fields = ('id', 'name', 'slug', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'attributes', 'is_leaf', 'view_class', 'structure', 'tagging_restriction', 'children')

    def get_tagging_restriction(self, instance):
        if instance.system_flags.external_tagging_restriction:
            return True
        else:
            return False
