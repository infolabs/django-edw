from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from django.db.utils import load_backend, ConnectionDoesNotExist
from django.db import connections, DEFAULT_DB_ALIAS


REPLICATION_UNHEALTHY_KEY = '__database_replication_unhealthy_aliases__'


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_slave_status(connection):
    status = {}
    with connection.cursor() as cursor:
        cursor.execute('SHOW SLAVE STATUS;')
        status = dictfetchall(cursor)[0]
    return status

def get_slave_connections():
    slave_connections = {}
    for alias, db in settings.REPLICA_DATABASES_ALL.items():
        try:
            slave_connection = connections[alias]
        except ConnectionDoesNotExist:
            db.setdefault('TIME_ZONE', None)
            db.setdefault('CONN_MAX_AGE', 0)
            db.setdefault('OPTIONS', {})
            db.setdefault('AUTOCOMMIT', True)
            backend = load_backend(db['ENGINE'])
            slave_connection = backend.DatabaseWrapper(db, alias)
        slave_connections[alias] = slave_connection
    return slave_connections


def get_slave_statuses():
    statuses = {}
    for alias, slave_connection in get_slave_connections().items():
        status = get_slave_status(slave_connection)
        statuses[alias] = status
    return statuses


class Command(BaseCommand):
    def handle(self, **options):
        slave_statuses = get_slave_statuses()
        unhealthy = []
        for alias, status in slave_statuses.items():
            if status['Slave_IO_Running'] == 'Yes' and status['Slave_SQL_Running'] == 'Yes':
                continue
            print('Replication failed for {}'.format(alias))
            unhealthy.append(alias)
        cache.set(REPLICATION_UNHEALTHY_KEY, unhealthy, None)
