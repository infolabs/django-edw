# -*- coding: utf-8 -*-
"""
E9/R5: settings for the bulk write-alias regression gate.

Same real-runtime matrix as ``edw_runtime_settings`` plus a *real* second
database alias and real router classes.  No router function is monkeypatched:
the tests flip ``route_all`` on the router object itself.
"""
from __future__ import unicode_literals

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = 'edw-safety-r5-alias-not-a-secret'
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
    'safety_alias_router.TermSecondAliasRouter',
    'safety_alias_router.ReadReplicaRouter',
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
    'edw.tests.contract.app',
    'edw',
)

MIDDLEWARE = ()

ROOT_URLCONF = 'safety_alias_urls'

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
