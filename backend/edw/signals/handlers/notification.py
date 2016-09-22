# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.utils.six.moves.urllib.parse import urlparse

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


def entity_event_notification(sender, instance=None, target=None, **kwargs):
    if not isinstance(instance, EntityModel.materialized):
        return
    for notification in Notification.objects.filter(transition_target=Notification.get_transition_target(sender, target)):
        recipient = notification.get_recipient(instance)
        if recipient is None:
            continue

        # emulate a request object which behaves similar to that one, when the customer submitted its order
        if instance.stored_request:
            emulated_request = EmulateHttpRequest(instance.customer, instance.stored_request)
            entity_serializer = EntityDetailSerializer(instance, context={'request': emulated_request})
            language = instance.stored_request.get('language')
            absolute_uri = emulated_request.build_absolute_uri().rstrip('/')
        else:
            entity_serializer = EntityDetailSerializer(instance)
            language = settings.LANGUAGE_CODE
            absolute_uri = instance.get_absolute_url()

        context = {
            'customer': CustomerSerializer(instance.customer).data,
            'data': entity_serializer.data,
            'ABSOLUTE_BASE_URI': absolute_uri,
            'render_language': language,
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