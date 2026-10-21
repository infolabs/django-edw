# -*- coding: utf-8 -*-
"""
E1: тестовая совместимость django-edw с установленным офлайн-стеком.

Модуль НЕ является частью продукта и не меняет семантику ядра. Он лишь
возвращает в процесс тестов те имена Django API, которые ядро ожидает
(Django 1.9/2.x), но которые удалены в Django 5.2, а также добавляет в
sys.path минимальные поставляемые с тестами заготовки отсутствующих
офлайн-пакетов (bitfield, rest_framework_bulk, rest_framework_filters,
rest_framework_recursive).

Импортируется до django.setup(), поэтому не должен импортировать edw.
"""
from __future__ import unicode_literals

import os
import sys

_APPLIED = False


def _install_django_aliases():
    from django.dispatch import Signal
    from django.utils import encoding, translation

    # ugettext* удалены в Django 4.0, замена 1:1 по смыслу.
    translation.ugettext = translation.gettext
    translation.ugettext_lazy = translation.gettext_lazy
    translation.ungettext = translation.ngettext
    translation.ungettext_lazy = translation.ngettext_lazy
    translation.ugettext_noop = translation.gettext_noop

    # force_text/smart_text удалены в Django 4.0.
    encoding.force_text = encoding.force_str
    encoding.smart_text = encoding.smart_str
    encoding.force_unicode = encoding.force_str

    # Signal(providing_args=...) удалён в Django 4.0.
    original_init = Signal.__init__
    if not getattr(original_init, '_edw_contract_compat', False):
        def compat_init(self, providing_args=None, use_caching=False):
            return original_init(self, use_caching=use_caching)

        compat_init._edw_contract_compat = True
        Signal.__init__ = compat_init


def _add_stubs_to_path():
    stubs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'edw', 'tests', 'contract', 'stubs')
    if stubs_dir not in sys.path:
        sys.path.insert(0, stubs_dir)


def install():
    """Идемпотентно устанавливает тестовую совместимость."""
    global _APPLIED
    if _APPLIED:
        return
    _add_stubs_to_path()
    _install_django_aliases()
    _APPLIED = True
