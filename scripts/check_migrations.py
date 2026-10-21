#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E4: проверки миграций django-edw на синтетическом контуре.

Скрипт запускается из ``scripts/check.sh`` отдельными процессами (режим в
аргументе), чтобы каждый сценарий начинал с чистой sqlite:

``drift``
    ``makemigrations --check --dry-run``: незапланированных миграций нет.
``apply``
    накат миграций на пустую файловую sqlite, ``migrate --check``,
    проверка таблиц и ORM-обращений (сериализация/права - в pytest).
``legacy``
    «синтетический снимок прежней схемы»: схема создаётся без миграций
    (``migrate --run-syncdb`` при ``MIGRATION_MODULES['edw_contracts']=None``),
    как у инсталляции, заведённой до появления миграций; печатается отпечаток
    схемы.
``fake``
    накат тех же миграций на legacy-схему через ``--fake-initial``;
    проверяется, что миграция записана, схема не изменилась, ORM работает.

pip/npm install, сеть и внешние БД не используются: только sqlite.
"""
from __future__ import unicode_literals

import json
import os
import sqlite3
import sys

APP_LABEL = 'edw_contracts'


def setup_django():
    import django

    # Совместимость импорта ядра и заглушки отсутствующих офлайн-пакетов
    # (bitfield и др.) нужны и при загрузке миграций.
    from edw_contract_compat import install

    install()
    django.setup()


def database_path():
    from django.conf import settings

    path = settings.DATABASES['default']['NAME']
    assert path and path != ':memory:', 'для проверок миграций нужна файловая sqlite'
    return path


def schema_tables():
    """Таблицы и колонки схемы (кроме служебных) как JSON-совместимый dict."""
    path = database_path()
    connection = sqlite3.connect(path)
    try:
        tables = {}
        rows = connection.execute(
            "select name from sqlite_master where type='table' "
            "and name not like 'sqlite_%' and name != 'django_migrations'"
        )
        for (name,) in rows:
            columns = tuple(sorted(row[1] for row in connection.execute(
                'pragma table_info("%s")' % name.replace('"', '""')
            )))
            tables[name] = columns
        return tables
    finally:
        connection.close()


def expected_tables():
    from django.apps import apps

    tables = set()
    for model in apps.get_app_config(APP_LABEL).get_models():
        tables.add(model._meta.db_table)
        for field in model._meta.local_many_to_many:
            through = field.remote_field.through
            if through is not None:
                tables.add(through._meta.db_table)
    return tables


def applied_contract_migrations():
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    return sorted(
        name for app_label, name in MigrationRecorder(connection).applied_migrations()
        if app_label == APP_LABEL
    )


def check_schema():
    actual = set(schema_tables())
    expected = expected_tables()
    missing = sorted(expected - actual)
    assert not missing, 'миграции не создали таблицы: {}'.format(missing)
    print('  таблиц в схеме {}: {}'.format(APP_LABEL, len(expected)))
    return expected


def orm_smoke():
    """Минимальные ORM-обращения к таблицам, созданным миграциями."""
    from django.contrib.auth.models import User

    from edw.models.defaults.term import Term
    from edw.rest.permissions import get_data_mart_permissions
    from edw.tests.contract.app.models import Customer, DataMart, DataMartPermission

    term = Term.objects.create(name='Smoke root', slug='smoke-root')
    data_mart = DataMart.objects.create(name='Smoke DM', slug='smoke-dm')
    user = User.objects.create_user('smoke-customer', password='secret')
    customer = Customer.objects.create(user=user, salutation='na')
    permission = DataMartPermission.objects.create(
        data_mart=data_mart, customer=customer, can_add=True, can_change=True, can_delete=False,
    )

    assert Term.objects.filter(pk=term.pk).exists()
    assert DataMart.objects.filter(pk=data_mart.pk).exists()
    assert DataMartPermission.objects.get(pk=permission.pk).can_delete is False

    from django.test import RequestFactory

    request = RequestFactory().get('/')
    request.user = user
    permissions_map = data_mart.get_permissions_from_request(request)
    assert permissions_map == {
        'can_add': True, 'can_change': True, 'can_delete': False, 'has_owner': True,
    }, permissions_map
    assert get_data_mart_permissions(request) is None
    print('  ORM: Term.DataMart.Customer.DataMartPermission читаются и пишутся')


def report_schema():
    print('SCHEMA:{}'.format(json.dumps(schema_tables(), sort_keys=True)))


def run_drift():
    from django.core.management import call_command

    try:
        call_command('makemigrations', check=True, dry_run=True, verbosity=0)
    except SystemExit:
        print('MIGRATION FAIL: обнаружены незапланированные миграции (makemigrations --check)')
        return 1
    print('MIGRATION OK: drift=0 (makemigrations --check --dry-run)')
    return 0


def run_apply():
    from django.core.management import call_command

    call_command('migrate', interactive=False, verbosity=0)
    call_command('migrate', check=True, verbosity=0)
    check_schema()
    assert applied_contract_migrations(), 'миграция {} не записана'.format(APP_LABEL)
    orm_smoke()
    report_schema()
    print('MIGRATION OK: накат на пустую sqlite: {}'.format(applied_contract_migrations()))
    return 0


def run_legacy():
    from django.conf import settings
    from django.core.management import call_command

    # Инсталляция, заведённая до появления миграций: таблицы создаёт syncdb.
    settings.MIGRATION_MODULES = {APP_LABEL: None}
    call_command('migrate', interactive=False, verbosity=0, run_syncdb=True)
    assert not applied_contract_migrations(), (
        'legacy-схема не должна содержать записей о миграциях {}'.format(APP_LABEL)
    )
    check_schema()
    report_schema()
    print('MIGRATION OK: синтетический снимок прежней схемы (без миграций)')
    return 0


def run_fake():
    from django.core.management import call_command

    call_command('migrate', interactive=False, verbosity=0, fake_initial=True)
    call_command('migrate', check=True, verbosity=0)
    applied = applied_contract_migrations()
    assert applied == ['0001_initial'], (
        'ожидалась запись {} 0001_initial, получено {}'.format(APP_LABEL, applied)
    )
    check_schema()
    orm_smoke()
    report_schema()
    print('MIGRATION OK: --fake-initial на прежней схеме: {}'.format(applied))
    return 0


MODES = {
    'drift': run_drift,
    'apply': run_apply,
    'legacy': run_legacy,
    'fake': run_fake,
}


def main(argv):
    if len(argv) != 2 or argv[1] not in MODES:
        print('usage: check_migrations.py {}'.format('|'.join(sorted(MODES))), file=sys.stderr)
        return 2
    if not os.environ.get('EDW_CONTRACT_DB'):
        print('MIGRATION FAIL: не задан EDW_CONTRACT_DB (нужна файловая sqlite)', file=sys.stderr)
        return 2
    setup_django()
    return MODES[argv[1]]()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
