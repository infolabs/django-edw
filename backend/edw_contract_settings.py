# -*- coding: utf-8 -*-
"""
E1: настройки синтетического контура для характеризационных тестов EDW.

Только sqlite в памяти, никаких внешних БД и сети. Настройки намеренно
минимальны: всё, что не нужно контрактам Entity/Term/DataMart/REST,
не подключается.
"""
from __future__ import unicode_literals

import os

from edw_contract_compat import install

install()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = 'edw-contract-tests-only-not-a-secret'
DEBUG = True
ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'ru'

# E4: миграционные проверки накатывают схему на файловую sqlite; тесты
# по-прежнему работают на sqlite в памяти (EDW_CONTRACT_DB не задан).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('EDW_CONTRACT_DB', ':memory:'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Ключевая настройка контракта материализации: все модели библиотеки
# материализуются в синтетическом приложении.
EDW_APP_LABEL = 'edw_contracts'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'polymorphic',
    'rest_framework',
    # Синтетическое приложение идёт до edw: его ready() прогревает cache-флаги,
    # чтобы AppConfig.ready() ядра не обращался к ещё не созданной тестовой БД.
    'edw.tests.contract.app',
    'edw',
)

MIDDLEWARE = ()

ROOT_URLCONF = 'edw.tests.contract.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': []},
    }
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

REST_FRAMEWORK = {
    'PAGE_SIZE': 10,
}
