# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import division

import re

from django.utils import six
from django import template
from django.template import TemplateSyntaxError

from classytags.core import Options, Tag
from classytags.arguments import Argument


register = template.Library()


RE_SIZE = re.compile(r'(\d+)x(\d+)$')


class GetAlignThumbnailInCenterStyles(Tag):
    name = 'get_align_thumbnail_in_center_styles'
    options = Options(
        Argument('size', required=True, resolve=True),
        Argument('width', required=True, resolve=True),
        Argument('height', required=True, resolve=True),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, size, width, height, varname):
        if isinstance(size, six.string_types):
            m = RE_SIZE.match(size)
            if m:
                size = (int(m.group(1)), int(m.group(2)))
            else:
                raise TemplateSyntaxError(
                    "%r is not a valid size." % size)
        size_ratio = size[1] / size[0]
        thumbnail_ratio = height / width
        outer = 'padding-top: {:.0f}%;'.format(size_ratio * 100)
        if size_ratio < thumbnail_ratio:
            gap = (1 - size_ratio / thumbnail_ratio) * 50
            inner = 'padding-left: {:.0f}%; padding-right: {:.0f}%;'.format(gap, gap)
        else:
            inner = 'padding-top: {:.0f}%;'.format((size_ratio - thumbnail_ratio) * 50)
        styles = {
            'outer': outer,
            'inner': inner
        }
        context[varname] = styles
        return ''

register.tag(GetAlignThumbnailInCenterStyles)