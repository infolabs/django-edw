# -*- coding: utf-8 -*-
"""
E7: settings for the real-runtime gate.

This module deliberately does not import ``edw_contract_compat`` and does not
put the E1 stub directory on ``sys.path``.  The gate installs the repaired
django-edw wheel into the prepared venv and runs these tests against the
installed package and the four real namespaces
(``bitfield``, ``rest_framework_bulk``, ``rest_framework_filters``,
``rest_framework_recursive``).
"""
from __future__ import unicode_literals

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = 'edw-runtime-tests-only-not-a-secret'
DEBUG = True
ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'ru'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('EDW_RUNTIME_DB', ':memory:'),
        'TEST': {'NAME': ':memory:'},
    },
    # E11/R5: a real second SQLite alias for the write-alias controls.  The
    # routers below are inert until a test enables them, so every other suite
    # keeps using ``default`` only.
    'second': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
}

DATABASE_ROUTERS = [
    'safety_probe_router.TermSecondAliasRouter',
    'safety_probe_router.ReadReplicaRouter',
    'safety_probe_router.ExplicitWriteDefaultRouter',
    'safety_probe_router.InstanceHintWriteRouter',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# All EDW abstract models materialize into the synthetic contracts app.
EDW_APP_LABEL = 'edw_contracts'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'polymorphic',
    'rest_framework',
    # Synthetic app first: its ready() warms EDW cache flags before the core
    # AppConfig.ready() touches the yet-absent test tables.
    'edw.tests.contract.app',
    'edw',
)

MIDDLEWARE = ()

ROOT_URLCONF = 'urls'

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
