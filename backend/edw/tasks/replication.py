from django.core.management import call_command

from io import StringIO
from celery import shared_task


@shared_task(name='replication_health')
def replication_health():
    out = StringIO()
    call_command('replication_health')
    result = out.getvalue()
    return result


@shared_task(name='replication_purge')
def replication_purge():
    out = StringIO()
    call_command('replication_purge')
    result = out.getvalue()
    return result
