# -*- coding: utf-8 -*-

from django import template

from edw.templatetags.edw_tags.common import (
    time, date, split, trim, multiply, bitwise_and,
    to_list, append_value, empty_str,
)
from edw.templatetags.edw_tags.entities import GetEntity, GetEntities
from edw.templatetags.edw_tags.data_marts import GetDataMart, GetDataMarts
from edw.templatetags.edw_tags.frontend import CompactJson, AddToSingletonJs, jsondumps
from edw.templatetags.edw_tags.term import GetTermTree, attributes_has_view_class

register = template.Library()

register.filter(time, expects_localtime=True, is_safe=False)
register.filter(date, expects_localtime=True, is_safe=False)
register.filter(split)
register.filter(trim)
register.filter(to_list)
register.filter(append_value)
register.filter(empty_str)
register.filter(multiply)
register.filter(bitwise_and)

register.tag(GetEntity)
register.tag(GetEntities)

register.tag(GetDataMart)
register.tag(GetDataMarts)

register.tag(CompactJson)
register.filter(jsondumps)
register.tag(AddToSingletonJs)

register.filter(attributes_has_view_class)
register.tag(GetTermTree)
