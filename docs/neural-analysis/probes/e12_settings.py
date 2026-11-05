# -*- coding: utf-8 -*-
"""E12.residualcheck: independent check settings (no author conftest imported)."""
from __future__ import unicode_literals

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = 'e12-independent-check-only-not-a-secret'
DEBUG = True
ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'ru'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
    'second': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
}

DATABASE_ROUTERS = [
    'e12_routers.SecondAliasRouter',
    'e12_routers.ReadReplicaRouter',
    'e12_routers.ExplicitWriteDefaultRouter',
    'e12_routers.InstanceHintWriteRouter',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

EDW_APP_LABEL = 'edw_contracts'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'polymorphic',
    'rest_framework',
    # synthetic materialized models first, same order as the product harness
    'edw.tests.contract.app',
    'edw',
)

MIDDLEWARE = ()

ROOT_URLCONF = 'e12_urls'

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
