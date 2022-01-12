from django.core.management.base import BaseCommand
from django.db import connection
from .replication_health import get_slave_statuses, dictfetchall


class Command(BaseCommand):
    def handle(self, **options):
        slave_statuses = get_slave_statuses()

        slave_binlogs = []
        for status in slave_statuses.values():
            slave_binlogs.append(status['Master_Log_File'])

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
