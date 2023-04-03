# -*- coding: utf-8 -*-

"""
Alternative implementation of Django's authentication User model, which allows to authenticate
against the email field in addition to the username fields.
This alternative implementation is activated by setting ``AUTH_USER_MODEL = 'edw.User'`` in
settings.py, otherwise the default Django or another customized implementation will be used.
"""

# standard library
from __future__ import unicode_literals
import logging

# Django
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):

    def _process_similar_email(self, username):
        single_user = self.filter(is_active=True, email=username).order_by('-date_joined').first()
        another_users_query = self.filter(is_active=True, email=username).exclude(id=single_user.id)
        similar_users_id = list(another_users_query.values_list('id', flat=True))
        another_users_query.update(is_active=False)
        logger = logging.getLogger('logfile_error')
        msg = 'Several users with the same email "{username}".' \
              ' One account remained active (id={active_user_id}),' \
              ' else users (id={nonactive_users_id}) set status' \
              ' "is_active=False")'.format(
                        username=username,
                        active_user_id=single_user.id,
                        nonactive_users_id=similar_users_id
                    )
        logger.error(msg)
        return single_user

    def get_by_natural_key(self, username):
        try:
            return self.get(username=username)
        except self.model.DoesNotExist:
            try:
                return self.get(is_active=True, email=username)
            except self.model.MultipleObjectsReturned:
                return self._process_similar_email(username)


class User(AbstractUser):
    """
    Alternative implementation of Django's User model allowing to authenticate against the email
    field in addition to the username field, which remains the primary unique identifier. The
    email field is only used in addition. It must be unique only for users marked as active.
    """
    patronymic = models.CharField(_("Patronymic"), max_length=255, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'auth_user'
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")

    def __str__(self):
        return self.username if self.is_staff else self.email or self.username

    def get_full_name(self):
        last_name = self.last_name if self.last_name is not None else ''
        first_name = self.first_name if self.first_name is not None else ''
        patronymic = self.patronymic if self.patronymic is not None else ''
        full_name = '{} {} {}'.format(last_name, first_name, patronymic)
        if full_name:
            return full_name.strip()
        return self.get_short_name()

    def get_short_name(self):
        short_name = super(User, self).get_short_name()
        if short_name:
            return short_name
        return self.email

    def validate_unique(self, exclude=None):
        """
        Since the email address is used as the primary identifier, we must ensure that it is
        unique. However, this can not be done on the field declaration since is only applies to
        active users. Inactive users can not login anyway, so we don't need a unique constraint
        for them.
        """
        super(User, self).validate_unique(exclude)
        if self.email and get_user_model().objects.exclude(id=self.id).filter(is_active=True, email__exact=self.email).exists():
            msg = _("A customer with the e-mail address ‘{email}’ already exists.")
            raise ValidationError({'email': msg.format(email=self.email)})


class BannedEmailDomain(models.Model):
    domain_name = models.CharField(
        max_length=255,
        verbose_name=_('Domain name'),
        unique=True,
        db_index=True,
    )

    class Meta:
        ordering = ('domain_name',)
        db_table = 'auth_banned_email_domain'
        verbose_name = _("Banned email domain")
        verbose_name_plural = _("Banned email domains")

    def __str__(self):
        return self.domain_name
