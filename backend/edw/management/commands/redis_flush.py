# -*- coding: utf-8 -*-
import re

from os.path import isfile
from subprocess import check_call
from celery import current_app

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    parameters_list = []

    def get_parameters(self, url):
        db = url.split('/')[-1]
        host = re.search(r'//(.+?):', url).group(1)
        self.parameters_list.append([db, host])

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

        # Redis DB number of Django cache
        default = settings.CACHES.get('default', {})
        backend = default.get('BACKEND', None)
        location = default.get('LOCATION', None)
        if backend == 'django_redis.cache.RedisCache':
            self.get_parameters(location)
        # Redis DB number of Celery broker
        broker_url = current_app.conf.broker_url
        if broker_url.startswith('redis'):
            self.get_parameters(broker_url)

        command = [
            executable_path,
            '-h'
        ]

        for params in self.parameters_list:
            db, host = params
            print('FLushing DB %s ...' % db)
            check_call(command + [host, '-n', db, 'FLUSHDB'])
        return 'Done'
