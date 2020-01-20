# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument

from edw.models.term import TermModel
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.rest.serializers.term import TermTreeSerializer


class GetTermTree(BaseRetrieveDataTag):
    name = 'get_term_tree'
    queryset = TermModel.objects.toplevel()
    serializer_class = TermTreeSerializer
    action = 'tree'

    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, kwargs, varname):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context=context)
        data = serializer.data
        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)


def attributes_has_view_class(value, arg):
    if value and isinstance(value, (tuple, list)):
        getter = (lambda x: x['view_class']) if isinstance(value[0], dict) else lambda x: x.view_class
        for attr in value:
            view_class = getter(attr)
            if arg in view_class:
                return True
    return False
