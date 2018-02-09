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
    class Meta:
        proxy = True


class EmailManager(models.Manager):
    def get_queryset(self):
        return Email.objects.get_queryset()

OriginalEmail.add_to_class('objects', EmailManager())