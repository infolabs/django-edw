from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from post_office.models import Email

import logging
logger = logging.getLogger('logfile')


@shared_task(name='delete_post_office_email')
def delete_post_office_email(days_to_save):

    res = {
        "success": 0,
        "error": []
    }

    emails = Email.objects.all().order_by('created')
    date_to_save_email = timezone.now() - timedelta(days=days_to_save)

    for email in emails:
        try:
            if date_to_save_email.date() > email.created.date():
                email.delete()
                res["success"] += 1
        except Exception as exc:
            res["error"].append(email.pk)
            logger.error(f"Error when deleting email id:{email.pk}. Error: {exc}")
    return res
