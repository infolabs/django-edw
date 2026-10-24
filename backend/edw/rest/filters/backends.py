# -*- coding: utf-8 -*-
"""
E7: explicit EDW filter backend.

``django-filter`` 26.x (used through ``rest_framework_filters`` 1.0.0.dev2)
resolves a filterset only from ``view.filterset_class`` / ``filterset_fields``.
The historical EDW attribute ``filter_class`` was silently ignored, so query
parameters did not change the queryset at all.

The backend below keeps exactly one explicit legacy path for third-party EDW
views that still declare ``filter_class``; the path is type-checked, model
checked and covered by the runtime tests.  Product views use
``filterset_class``.
"""
from __future__ import unicode_literals

try:
    from rest_framework_filters.backends import RestFrameworkFilterBackend as _FilterBackendBase
except ImportError:  # coverage for the historical package layout
    from rest_framework_filters.backends import DjangoFilterBackend as _FilterBackendBase


class EDWFilterBackend(_FilterBackendBase):
    """
    RestFramework-compatible filterset backend with an explicit legacy alias.

    ``filterset_class`` is the supported attribute.  ``filter_class`` is kept
    as a documented compatibility path: it must be a filterset class, and its
    ``Meta.model`` must accept the filtered queryset.  Nothing is inherited
    silently from an unvalidated attribute.
    """

    legacy_filter_class_attr = 'filter_class'

    def get_filterset_class(self, view, queryset=None):
        parent = getattr(super(EDWFilterBackend, self), 'get_filterset_class', None)
        if parent is not None:
            filterset_class = parent(view, queryset)
            if filterset_class is not None:
                return filterset_class

        legacy = getattr(view, self.legacy_filter_class_attr, None)
        if legacy is None:
            return None
        if not isinstance(legacy, type) or not issubclass(legacy, self.filterset_base):
            raise TypeError(
                '{} must be a {} subclass, got {!r}'.format(
                    self.legacy_filter_class_attr, self.filterset_base.__name__, legacy
                )
            )
        model = getattr(getattr(legacy, '_meta', None), 'model', None)
        if model is not None and queryset is not None:
            if not issubclass(queryset.model, model):
                raise TypeError(
                    '{} model {!r} does not match queryset model {!r}'.format(
                        self.legacy_filter_class_attr, model, queryset.model
                    )
                )
        return legacy


# Keep the historical import name used by EDW views/templatetags.
DjangoFilterBackend = EDWFilterBackend
