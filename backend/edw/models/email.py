#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from post_office.models import Email as OriginalEmail


class Email(OriginalEmail):
    class Meta:
        """
        ENG: Proxy model is used to modify the behavior of the model.
        RUS: Proxy-модель для изменения поведения модели.
        """
        proxy = True


class EmailManager(models.Manager):
    """
    ENG: Application EmailManager to manage emails sent by a Django application.
    RUS: Приложение Менеджер почты. Управляет электронными письмами, отправленными приложением Django.
    """
    def get_queryset(self):
        """
        ENG: Return QuerySet a list of email objects
        RUS: Возвращает в запросе список имеющихся email.
        """
        return Email.objects.get_queryset()

OriginalEmail.add_to_class('objects', EmailManager())