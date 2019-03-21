# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from functools import reduce

from classytags.core import Tag
from classytags.core import Options
from classytags.arguments import Argument
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text


class CompactJson(Tag):
    name = 'compactjson'

    options = Options(
        'as',
        Argument('varname', required=False, resolve=False),
        blocks=[('endcompactjson', 'nodelist')]
    )

    def render_tag(self, context, nodelist, varname):
        def ren(x):
            ret = x.render(context)
            return ret

        def tex(x, y):
            ret = x + smart_text(y)
            return ret

        block_data = reduce(
            tex,
            map(
                ren,
                nodelist
            )
        )
        block_data = json.loads(block_data)
        block_data = json.dumps(block_data)
        if varname:
            context[varname] = block_data
            return ''
        else:
            return mark_safe(block_data)


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


def jsondumps(value):
    """Return the string split by separator.

    Example usage: {{ value|jsondumps }}
    """
    res = json.dumps(value, ensure_ascii=False, cls=LazyEncoder)
    res = res.encode('utf-8')
    return mark_safe(res)


class AddToSingletonJs(Tag):
    name = 'addtosingeltonjs'

    BEFORE = """<script>
var _key = "_global_singleton_instance",
    instance = window[_key];
!instance && (instance = window[_key] = {});"""
    AFTER = '</script>'

    options = Options(
        "as",
        Argument("varname", required=False, resolve=False),
        blocks=[("endaddtosingeltonjs", "nodelist")]
    )

    def render_tag(self, context, nodelist, varname):
        block_data = self.BEFORE + nodelist.render(context) + self.AFTER
        if varname:
            context[varname] = block_data
            return ''
        else:
            return block_data
