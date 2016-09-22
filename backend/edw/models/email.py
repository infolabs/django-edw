#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template

from django.utils.encoding import smart_text
from django.utils.translation import override as translation_override

from bs4 import BeautifulSoup

from post_office.models import Email as OriginalEmail


class Email(OriginalEmail):
    """
    Patch class `post_office.models.Email` which fixes https://github.com/ui/django-post_office/issues/116
    and additionally converts HTML messages into plain text messages.
    """
    class Meta:
        proxy = True

    def email_message(self, connection=None):
        subject = smart_text(self.subject)

        if self.template is not None:
            render_language = self.context.get('render_language', settings.LANGUAGE_CODE)
            context = Context(self.context)
            with translation_override(render_language):
                subject = Template(self.template.subject).render(context)
                message = Template(self.template.content).render(context)
                html_message = Template(self.template.html_content).render(context)
        else:
            subject = self.subject
            message = self.message
            html_message = self.html_message

        if html_message:
            if not message:
                message = BeautifulSoup(html_message).text
            mailmsg = EmailMultiAlternatives(
                subject=subject, body=message, from_email=self.from_email,
                to=self.to, bcc=self.bcc, cc=self.cc,
                connection=connection, headers=self.headers)
            mailmsg.attach_alternative(html_message, 'text/html')
        else:
            mailmsg = EmailMessage(
                subject=subject, body=message, from_email=self.from_email,
                to=self.to, bcc=self.bcc, cc=self.cc,
                connection=connection, headers=self.headers)

        for attachment in self.attachments.all():
            mailmsg.attach(attachment.name, attachment.file.read())
        return mailmsg


class EmailManager(models.Manager):
    def get_queryset(self):
        return Email.objects.get_queryset()

OriginalEmail.add_to_class('objects', EmailManager())