# -*- coding: utf-8 -*-

from os.path import isfile
from subprocess import check_call
from celery import current_app

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, **options):
        possible_executables = [
            'redis-cli',
            '/usr/bin/redis-cli',
        ]
        for executable_path in possible_executables:
            if isfile(executable_path):
                break
        else:
            raise CommandError('Couldn\'t find redis-cli executable')

        dbs = []
        # Redis DB number of Django cache
        default = settings.CACHES.get('default', {})
        backend = default.get('BACKEND', None)
        location = default.get('LOCATION', None)
        if backend == 'django_redis.cache.RedisCache':
            dbs.append(location.split('/')[-1])
        # Redis DB number of Celery broker
        broker_url = current_app.conf.broker_url
        if broker_url.startswith('redis'):
            dbs.append(broker_url.split('/')[-1])

        command = [
            executable_path,
            '-h', 'redis',
        ]
        for db in dbs:
            print('FLushing DB %s ...' % db)
            check_call(command + ['-n', db, 'FLUSHDB'])
        return 'Done'
