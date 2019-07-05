#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import SerializerMethodField

from edw.rest.serializers.term import TermTreeSerializer


class WidgetTermTreeSerializer(TermTreeSerializer):
    """
    ENG: Widget Term Tree Serializer
    RUS: Приложение - сериалайзер терминов дерева
    """
    tagging_restriction = SerializerMethodField()

    class Meta(TermTreeSerializer.Meta):
        """
        Метаданные сериалайзера терминов дерева
        """
        fields = ('id', 'name', 'slug', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'attributes', 'is_leaf', 'view_class', 'structure', 'tagging_restriction', 'children')

    def get_tagging_restriction(self, instance):
        """
        Возвращает системные флаги ограничения тегов
        """
        return bool(instance.system_flags.external_tagging_restriction)
