# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from rest_framework.settings import api_settings

APP_LABEL = settings.EDW_APP_LABEL  # mandatory setting without default


GUEST_IS_ACTIVE_USER = getattr(settings, 'EDW_GUEST_IS_ACTIVE_USER', False)
"""
If ``EDW_GUEST_IS_ACTIVE_USER`` is True, Customers which declared themselves as guests, may request
a password reset, so that they can log into their account at a later time. The default is False.
"""


CACHE_DURATIONS = {
    'data_mart_children': 3600,
    'data_mart_all_active_terms': 3600,
    'data_mart_html_snippet': 86400,
    'data_mart_validate_term_model': 60,

    'term_decompress': 3600,
    'term_children': 3600,
    'term_ancestors': 3600,
    'term_all_attribute_descendants_ids': 3600,
    'term_attribute_ancestors': 3600,
    'term_all_active_root_ids': 3600,

    'entity_html_snippet': 86400,
    'entity_terms_ids': 3600,
    'entity_data_mart': 3600,
    'entity_validate_term_model': 60,
    'entity_validate_data_mart_model': 60,
}
CACHE_DURATIONS.update(getattr(settings, 'EDW_CACHE_DURATIONS', {}))


CACHE_BUFFERS_SIZES = {
    'term_decompress': 500,
    'term_children': 500,
    'term_attribute_ancestors': 1000,

    'data_mart_children': 500,

    'entity_terms_ids': 500,
    'entity_data_mart': 500,
}
CACHE_BUFFERS_SIZES.update(getattr(settings, 'EDW_CACHE_BUFFERS_SIZES', {}))


REST_PAGINATION = {
    'data_mart_default_limit': api_settings.PAGE_SIZE,
    'data_mart_max_limit': 500,

    'term_default_limit': api_settings.PAGE_SIZE,
    'term_max_limit': 500,

    'entity_default_limit': api_settings.PAGE_SIZE,
    'entity_max_limit': 500,
}
REST_PAGINATION.update(getattr(settings, 'EDW_REST_PAGINATION', {}))


REGISTRATION_PROCESS = {
    'registration_salt': 'registration',
    'do_activation': False,
    'account_activation_days': 5
}
REGISTRATION_PROCESS.update(getattr(settings, 'EDW_REGISTRATION_PROCESS', {}))


SEMANTIC_FILTER = {
    'fast_subquery_results_limit': 1000,
    'fast_subquery_filters_default': 3
}
SEMANTIC_FILTER.update(getattr(settings, 'EDW_SEMANTIC_FILTER', {}))
