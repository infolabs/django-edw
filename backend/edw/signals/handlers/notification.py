# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.utils.six.moves.urllib.parse import urlparse
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from post_office import mail
from post_office.models import EmailTemplate

from django_fsm.signals import post_transition

from edw.models.entity import EntityModel
from edw.models.notification import Notification

from edw.rest.serializers.entity import EntityDetailSerializer
from edw.rest.serializers.customer import CustomerSerializer


class EmulateHttpRequest(HttpRequest):
    """
    Use this class to emulate a HttpRequest object, when templates must be rendered
    asynchronously, for instance when an email must be generated out of an Order object.
    """
    def __init__(self, customer, stored_request):
        super(EmulateHttpRequest, self).__init__()
        parsedurl = urlparse(stored_request.get('absolute_base_uri'))
        self.path = self.path_info = parsedurl.path
        self.environ = {}
        self.META['PATH_INFO'] = parsedurl.path
        self.META['SCRIPT_NAME'] = ''
        self.META['HTTP_HOST'] = parsedurl.netloc
        self.META['HTTP_X_FORWARDED_PROTO'] = parsedurl.scheme
        self.META['QUERY_STRING'] = parsedurl.query
        self.META['HTTP_USER_AGENT'] = stored_request.get('user_agent')
        self.META['REMOTE_ADDR'] = stored_request.get('remote_ip')
        self.method = 'GET'
        self.LANGUAGE_CODE = self.COOKIES['django_language'] = stored_request.get('language')
        self.customer = customer
        self.user = customer.is_anonymous() and AnonymousUser or customer.user
        self.current_page = None

email_validator = EmailValidator()

def entity_event_notification(sender, instance=None, **kwargs):
    if not isinstance(instance, EntityModel.materialized):
        return

    target = kwargs['target']
    for notification in Notification.objects.filter(transition_target=Notification.get_transition_target(sender, target)):
        recipient = instance.get_recipient(notification.mail_to)

        if recipient is None:
            continue

        try:
            email_validator(recipient)
        except ValidationError:
            default_email = getattr(settings, "DEFAULT_TO_EMAIL", None)
            if default_email:
                recipient = default_email
            else:
                continue

        # emulate a request object which behaves similar to that one, when the customer submitted its order
        stored_request = instance.stored_request[0] if isinstance(instance.stored_request, (tuple, list)) else instance.stored_request
        emulated_request = EmulateHttpRequest(instance.customer, stored_request)
        entity_serializer = EntityDetailSerializer(instance, context={'request': emulated_request})
        language = stored_request.get('language')
        context = {
            'customer': CustomerSerializer(instance.customer).data,
            'data': entity_serializer.data,
            'ABSOLUTE_BASE_URI': emulated_request.build_absolute_uri().rstrip('/'),
            'render_language': language,
            'transition': {
                'name': kwargs['name'],
                'source': kwargs['source'],
                'target': target
            }
        }
        try:
            template = notification.mail_template.translated_templates.get(language=language)
        except EmailTemplate.DoesNotExist:
            template = notification.mail_template
        attachments = {}
        for notiatt in notification.notificationattachment_set.all():
            attachments[notiatt.attachment.original_filename] = notiatt.attachment.file.file
        mail.send(recipient, template=template, context=context,
                  attachments=attachments, render_on_delivery=True)

post_transition.connect(entity_event_notification)
