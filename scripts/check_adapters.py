#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E4: smoke-проверка адаптеров зависимостей на целевой матрице G0.1.

Проверяется то, что можно проверить офлайн и без admin-приложения:
* django-filer 3.6 + DRF 3.18: сериализаторное поле файла и владелец;
* django-filter 26.x: адаптер аргумента ``name`` и CSV-виджет EDW;
* django-fsm-2: модуль django_fsm и сигнал post_transition;
* django-mptt / django-polymorphic / django-select2 импортируются.

Адаптеры, которым нужны не поставленные в офлайн-venv библиотеки
(rest_framework_filters, bitfield, rest_auth, haystack, celery и др.),
помечаются ADAPTER SKIP: это зафиксировано в отчёте, а не скрыто.
"""
from __future__ import unicode_literals

import importlib


def configure():
    from django.conf import settings

    settings.configure(
        SECRET_KEY='edw-dependency-adapters-check',
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
        USE_TZ=True,
        TIME_ZONE='UTC',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'easy_thumbnails',
            'filer',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        STATIC_URL='/static/',
    )

    import django

    django.setup()


class UserStub(object):
    def __init__(self, is_authenticated):
        self.is_authenticated = is_authenticated


class RequestStub(object):
    def __init__(self, user):
        self.user = user


def check_filer_serializer():
    from rest_framework import serializers

    from edw.rest.serializers.filer_fields import FilerFileField

    class UploadSerializer(serializers.Serializer):
        file = FilerFileField(upload_folder_name='edw-adapters-check', required=False)

    anonymous = UserStub(is_authenticated=False)
    authenticated = UserStub(is_authenticated=True)

    without_request = UploadSerializer(context={'request': None})
    assert without_request.fields['file'].get_owner(None) is None

    with_anonymous = UploadSerializer(context={'request': RequestStub(anonymous)})
    assert with_anonymous.fields['file'].get_owner(None) is None

    with_user = UploadSerializer(context={'request': RequestStub(authenticated)})
    assert with_user.fields['file'].get_owner(None) is authenticated

    # django-filer установлен в матрице, значит класс права обязан быть объявлен.
    from rest_framework.permissions import BasePermission

    from edw.rest.permissions import IsFilerFileOwnerOrReadOnly

    assert issubclass(IsFilerFileOwnerOrReadOnly, BasePermission)
    print('ADAPTER OK: django-filer 3.x -> FilerFileField/IsFilerFileOwnerOrReadOnly')


def check_django_filter():
    from django_filters.filters import Filter

    from edw.rest.filters.common import parse_null_boolean
    from edw.rest.filters.widgets import CSVWidget

    filter_ = Filter(name='created_at', lookup_expr='exact')
    assert filter_.field_name == 'created_at'
    filter_ = Filter(name='created_at', field_name='updated_at', lookup_expr='exact')
    assert filter_.field_name == 'updated_at'

    widget = CSVWidget()
    assert widget.value_from_datadict({'value': '1,2'}, {}, 'value') == ['1', '2']
    assert widget.value_from_datadict({}, {}, 'value') is None

    assert parse_null_boolean('t') is True
    assert parse_null_boolean('0') is False
    assert parse_null_boolean('') is None
    print('ADAPTER OK: django-filter 26.x -> Filter(name=...), CSVWidget, parse_null_boolean')


def check_fsm():
    import django_fsm

    assert hasattr(django_fsm, 'RETURN_VALUE')
    assert hasattr(django_fsm, 'FSMField')
    assert hasattr(django_fsm, 'transition')
    from django_fsm.signals import post_transition  # noqa: F401

    print('ADAPTER OK: django-fsm-2 -> django_fsm.RETURN_VALUE/FSMField/post_transition')


def check_core_imports():
    import django_select2  # noqa: F401
    import mptt  # noqa: F401
    import polymorphic  # noqa: F401

    print('ADAPTER OK: django-mptt / django-polymorphic / django-select2 импортируются')


def report_skipped():
    """Адаптеры библиотек, отсутствующих в офлайн-venv: их подменяют заглушки E1."""
    missing = (
        'rest_framework_filters',
        'rest_framework_bulk',
        'rest_framework_recursive',
        'rest_auth',
        'bitfield',
        'salmonella',
        'dynamic_raw_id',
        'django_mptt_admin',
        'haystack',
        'celery',
        'social_core',
    )
    skipped = []
    for module_name in missing:
        try:
            importlib.import_module(module_name)
        except ImportError:
            skipped.append(module_name)
    if skipped:
        print('ADAPTER SKIP: нет в офлайн-venv (тесты E1 используют заглушки): {}'.format(
            ', '.join(skipped)
        ))
    return skipped


def main():
    configure()
    check_core_imports()
    check_django_filter()
    check_fsm()
    check_filer_serializer()
    report_skipped()
    print('ADAPTERS PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
