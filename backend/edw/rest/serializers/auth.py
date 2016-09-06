# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.template.loader import select_template
from rest_framework.serializers import CharField, ModelSerializer as RestModelSerializer
from rest_auth import serializers
from edw import settings as edw_settings
from django.contrib.auth import get_user_model


class PasswordResetSerializer(serializers.PasswordResetSerializer):
    def save(self):
        subject_template = select_template([
            '{}/email/reset-password-subject.txt'.format(edw_settings.APP_LABEL),
            'edw/email/reset-password-subject.txt',
        ])
        body_template = select_template([
            '{}/email/reset-password-body.txt'.format(edw_settings.APP_LABEL),
            'edw/email/reset-password-body.txt',
        ])
        opts = {
            'use_https': self.context['request'].is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': self.context['request'],
            'subject_template_name': subject_template.template.name,
            'email_template_name': body_template.template.name,
        }
        self.reset_form.save(**opts)


class PasswordResetConfirmSerializer(serializers.PasswordResetConfirmSerializer):
    new_password1 = CharField(min_length=6, max_length=128)
    new_password2 = CharField(min_length=6, max_length=128)


"""
class RegistrationSerializer(RestModelSerializer):
    password1 = CharField(min_length=6, max_length=128)
    password2 = CharField(min_length=6, max_length=128)
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self):
        self.set_password_form.save()
"""
