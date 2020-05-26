# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404

from rest_framework.generics import get_object_or_404 as _get_object_or_404


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as DRF standard shortcut, but make sure to also raise 404
    if the returned more than one object.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except MultipleObjectsReturned:
        raise Http404
