from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext

from edw.tasks.delete_post_office_email import delete_post_office_email

import logging

logger = logging.getLogger('logfile')


class Command(BaseCommand):
    help = ugettext("Delete history to emails")

    def add_arguments(self, parser):
        parser.add_argument(
            '--days_to_save',
            dest='days_to_save',
            type=int,
            default=180,
            help=ugettext('Count days to save emails')
        )

    def handle(self, *args, **options):
        days_to_save = options.get('days_to_save')

        if days_to_save < 0:
            raise CommandError(ugettext('`days_to_save` must be positive'))

        result = delete_post_office_email(days_to_save)
        print(f"Successfully removed {result['success']} emails\n"
              f"Error on deleting for emails {result['error']}")
