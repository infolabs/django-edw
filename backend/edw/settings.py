# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings


APP_LABEL = settings.EDW_APP_LABEL  # mandatory setting without default


GUEST_IS_ACTIVE_USER = getattr(settings, 'EDW_GUEST_IS_ACTIVE_USER', False)
"""
If ``EDW_GUEST_IS_ACTIVE_USER`` is True, Customers which declared themselves as guests, may request
a password reset, so that they can log into their account at a later time. The default is False.
"""


CACHE_DURATIONS = {
    'data_mart_children': 3600,

    'term_decompress': 3600,
    'term_children': 3600,
    'term_ancestors': 3600,
    'term_attribute_descendants_ids': 3600,
    'term_attribute_ancestors': 3600,

    'entity_html_snippet': 86400,
}
CACHE_DURATIONS.update(getattr(settings, 'EDW_CACHE_DURATIONS', {}))