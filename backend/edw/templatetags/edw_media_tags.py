# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import division

import re
import six

from django import template
from django.core.files import File
from django.contrib.staticfiles import finders
from django.template import TemplateSyntaxError

from classytags.core import Options, Tag
from classytags.arguments import Argument


register = template.Library()

RE_SIZE = re.compile(r'(\d+)x(\d+)$')

try:
    from filer.models import Image
except (ImportError, RuntimeError):
    pass
else:
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


try:
    from easy_thumbnails.files import get_thumbnailer
except (ImportError, RuntimeError):
    pass
else:
    class GetDefaultThumbnail(Tag):
        name = 'get_default_thumbnail'
        options = Options(
            Argument('size', required=True, resolve=True),
            Argument('replace_alpha', required=True, resolve=True),
            'as',
            Argument('varname', required=False, resolve=False)
        )

        def render_tag(self, context, size, replace_alpha, varname):
            if isinstance(size, six.string_types):
                m = RE_SIZE.match(size)
                if m:
                    size = (int(m.group(1)), int(m.group(2)))
                else:
                    raise TemplateSyntaxError(
                        "%r is not a valid size." % size)
            no_photo_name = "no_photo.png"
            no_photo_images = Image.objects.filter(original_filename=no_photo_name)
            if len(no_photo_images)!=0:
                no_photo_image = no_photo_images[0]
            else:
                no_photo_file = finders.find('edw/img/no_photo.png')
                with open(no_photo_file, "rb") as f:
                    file_obj = File(f, name=no_photo_name)
                    (no_photo_image, is_created) = Image.objects.get_or_create(
                        original_filename=no_photo_name,
                        defaults={'file': file_obj, 'owner': context.request.user}
                    )
            thumbnailer = get_thumbnailer(no_photo_image)
            thumbnail_options = {
                'crop': True,
                "size": size,
                "replace_alpha": replace_alpha,
                "upscale": True,
            }
            thumb = thumbnailer.get_thumbnail(thumbnail_options)
            context[varname] = thumb
            return ''

    register.tag(GetDefaultThumbnail)
