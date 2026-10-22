# -*- coding: utf-8 -*-
"""
E5.fix: регрессия по API, удалённым в Django 5.0/5.1.

E6 нашёл в продуктовом коде два вызова, которых нет в целевом стеке
(Django 5.2 LTS):
* `utc` из `django.utils.timezone` (удалён в Django 5.0) — UTC-конвертация
  в `edw/utils/dateutils.py`;
* `UserManager.make_random_password()` (удалён в Django 5.1) — генерация
  пароля в `edw/forms/auth.py`.

Тесты фиксируют замены (UTC из `datetime`, `django.utils.crypto.get_random_string`)
и статический барьер: ни одного из удалённых имён в продуктовом коде пакета edw.
"""
from __future__ import unicode_literals

import datetime
import io
import os
import re
import string
import types

import edw
from edw.forms import auth as edw_auth
from edw.utils import dateutils


EDW_PACKAGE_DIR = os.path.dirname(os.path.abspath(edw.__file__))

# Удалённые имена. Левее `timezone` не должно быть `_` или `.`: именно так
# выглядят допустимые замены — `datetime_timezone.utc` и `datetime.timezone.utc`.
REMOVED_API_PATTERNS = (
    ('django.utils.timezone.utc', re.compile(r'(?<![A-Za-z0-9_.])timezone\s*\.\s*utc')),
    ('from django.utils.timezone import utc', re.compile(r'(?<![A-Za-z0-9_])timezone\s+import\s+utc')),
    ('UserManager.make_random_password', re.compile(r'make_random_password')),
)


def product_python_files():
    """Продуктовые *.py пакета edw — без тестовой обвязки и кэша байткода."""
    for root, dirs, files in os.walk(EDW_PACKAGE_DIR):
        dirs[:] = sorted(name for name in dirs if name not in ('tests', '__pycache__'))
        for name in sorted(files):
            if name.endswith('.py'):
                yield os.path.join(root, name)


def read_module_source(module):
    with io.open(os.path.abspath(module.__file__), encoding='utf-8') as source:
        return source.read()


def assert_no_removed_api(source, where):
    found = [
        label for label, pattern in REMOVED_API_PATTERNS
        if pattern.search(source)
    ]
    assert not found, '{}: остались удалённые в Django 5.0/5.1 имена {}'.format(where, found)


def test_removed_api_is_absent_in_target_stack():
    """Барьер осмыслен только пока в целевом Django этих имён действительно нет."""
    from django.utils import timezone as django_timezone

    assert not hasattr(django_timezone, 'utc'), 'в Django вернулся timezone.utc'

    import django.utils.crypto as django_crypto

    assert hasattr(django_crypto, 'get_random_string'), (
        'нет замены удалённому make_random_password: django.utils.crypto.get_random_string'
    )


def test_datetime_to_local_converts_utc_moment():
    """
    `datetime_to_local` трактует naive-время как UTC и отдаёт текущий пояс.

    До E5.fix вызов падал с AttributeError (utc удалён в Django 5.0), поэтому
    проверяется и сам вызов, и перенос момента без сдвига.
    """
    naive = datetime.datetime(2020, 3, 1, 12, 30, 15)

    converted = dateutils.datetime_to_local(naive)

    assert converted.tzinfo is not None
    assert converted.utcoffset() == dateutils.local_tz.utcoffset(converted)
    assert converted == naive.replace(tzinfo=datetime.timezone.utc)
    # Замена tzinfo идёт через replace(): аргумент не мутирует, вызов повторяем.
    assert naive.tzinfo is None
    assert dateutils.datetime_to_local(naive) == converted


def test_datetime_to_local_keeps_aware_input_moment_offset():
    """Осознанное ограничение текущего кода: aware-аргумент переразмечается как UTC."""
    msk_offset = datetime.timezone(datetime.timedelta(hours=3))
    aware = datetime.datetime(2020, 3, 1, 12, 30, 15, tzinfo=msk_offset)

    converted = dateutils.datetime_to_local(aware)

    # Тот же wall time (replace, а не astimezone) — так ведёт себя код с E1.
    assert converted.replace(tzinfo=None) == aware.replace(tzinfo=None)
    assert converted != aware


def test_dateutils_uses_utc_from_datetime():
    source = read_module_source(dateutils)

    assert_no_removed_api(source, 'edw/utils/dateutils.py')
    assert 'datetime_timezone.utc' in source, 'UTC-конвертация должна брать UTC из datetime'


def make_register_form_data(**overrides):
    data = {
        'preset_password': True,
        'fio': 'Иванов Иван',
        'email': 'user@example.com',
    }
    data.update(overrides)
    return data


def test_register_form_generates_random_password(monkeypatch):
    """
    `preset_password=True` заполняет password1/password2 случайным паролем.

    Продуктовый constance-конфиг в контрактном контуре не поднимается (его
    бэкенд требует Redis), поэтому подменяется только объект конфига; сам путь
    генерации пароля остаётся продуктовым.
    """
    monkeypatch.setattr(edw_auth, 'config', types.SimpleNamespace(ALLOW_LOCALITY=False))

    def build():
        data = make_register_form_data()
        edw_auth.RegisterUserForm(data=data)
        return data

    first, second = build(), build()
    password = first['password1']

    assert password == first['password2'], 'пароль должен попасть в оба поля'
    min_length = edw_auth.RegisterUserForm.base_fields['password1'].min_length
    assert len(password) >= max(min_length, 8)
    assert set(password) <= set(string.ascii_letters + string.digits), (
        'get_random_string должен генерировать пароль из ascii-букв и цифр'
    )
    assert first['password1'] != second['password1'], 'пароль должен быть случайным'


def test_register_form_keeps_explicit_passwords(monkeypatch):
    """Без preset_password пароли из формы не перезаписываются."""
    monkeypatch.setattr(edw_auth, 'config', types.SimpleNamespace(ALLOW_LOCALITY=False))

    data = make_register_form_data(preset_password=False, password1='secret-1', password2='secret-1')
    edw_auth.RegisterUserForm(data=data)

    assert (data['password1'], data['password2']) == ('secret-1', 'secret-1')


def test_auth_form_uses_get_random_string():
    source = read_module_source(edw_auth)

    assert_no_removed_api(source, 'edw/forms/auth.py')
    assert 'get_random_string' in source, 'генерация пароля должна идти через django.utils.crypto'


def test_no_removed_api_in_product_code():
    """Статический барьер: удалённых имён нет ни в одном продуктовом модуле edw."""
    offenders = []
    for path in product_python_files():
        with io.open(path, encoding='utf-8') as source_file:
            source = source_file.read()
        for label, pattern in REMOVED_API_PATTERNS:
            if pattern.search(source):
                offenders.append('{}: {}'.format(os.path.relpath(path, EDW_PACKAGE_DIR), label))

    assert not offenders, 'в продуктовом коде остались удалённые API: {}'.format(offenders)
