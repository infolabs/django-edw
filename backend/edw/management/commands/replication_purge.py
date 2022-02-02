from django.core.management.base import BaseCommand
from django.db import connection
from .replication_health import get_slave_connections, get_slave_status, dictfetchall


class Command(BaseCommand):
    def handle(self, **options):
        slave_binlogs = []
        for alias, slave_connection in get_slave_connections().items():
            status = get_slave_status(slave_connection)
            slave_binlogs.append(status['Master_Log_File'])
            # flush relay logs
            with slave_connection.cursor() as cursor:
                cursor.execute('FLUSH LOGS;')

        # Get oldest binlog in use. Purge prior binlogs
        with connection.cursor() as cursor:
            target_binlog = None
            cursor.execute('SHOW BINARY LOGS;')
            logs = dictfetchall(cursor)
            for row in logs:
                name = row['Log_name']
                if name in slave_binlogs:
                    target_binlog = name
                    break
            if target_binlog:
                print('Purging binary logs to {}'.format(target_binlog))
                # the SQL statement needs SUPER privilege for a db user
                cursor.execute("PURGE BINARY LOGS TO '{}';".format(target_binlog))
