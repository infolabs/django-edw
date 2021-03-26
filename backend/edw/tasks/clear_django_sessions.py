from django.core.management import call_command

from io import StringIO
from celery import shared_task


@shared_task(name='clear_django_sessions')
def clear_django_sessions():
    out = StringIO()
    call_command('clearsessions')
    result = out.getvalue()
    return result
