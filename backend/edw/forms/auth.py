# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site

from django.core import signing
from django.core.exceptions import ValidationError

from django.forms import fields, widgets, ModelForm

from django.template import Context
from django.template.loader import select_template

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from edw import settings as edw_settings
from edw.models.customer import CustomerModel
from edw.signals.auth import customer_registered


class RegisterUserForm(ModelForm):
    form_name = 'register_user_form'

    fio = fields.CharField(label=_("Your fullname"), help_text=_("Example: Ivanov Ivan"), max_length=255)
    email = fields.EmailField(label=_("Your e-mail address"),
                              help_text=_("E-mail address is used as login"))
    preset_password = fields.BooleanField(required=False, label=_("Preset password"),
        widget=widgets.CheckboxInput(),
        help_text=_("Send a randomly generated password to your e-mail address"))

    password1 = fields.CharField(label=_("Choose a password"), widget=widgets.PasswordInput,
                                 min_length=6, help_text=_("Minimum length is 6 characters."))
    password2 = fields.CharField(label=_("Repeat password"), widget=widgets.PasswordInput,
                                 min_length=6, help_text=_("Confirm password."))

    class Meta:
        model = CustomerModel
        fields = ('fio', 'email', 'password1', 'password2',)

    def __init__(self, data=None, instance=None, *args, **kwargs):
        if data and data.get('preset_password', False):
            pwd_length = max(self.base_fields['password1'].min_length, 8)
            password = get_user_model().objects.make_random_password(pwd_length)
            data['password1'] = data['password2'] = password
        super(RegisterUserForm, self).__init__(data=data, instance=instance, *args, **kwargs)

    def clean_email(self):
        # check for uniqueness of email address
        if get_user_model().objects.filter(email=self.cleaned_data['email']).exists():
            msg = _("A customer with the e-mail address ‘{email}’ already exists.\n"
                    "If you have used this address previously, try to reset the password.")
            raise ValidationError(msg.format(**self.cleaned_data))
        return self.cleaned_data['email']

    def clean_fio(self):
        # check for fio
        #fio = self.cleaned_data['fio'].split(' ')
        #if len(fio) < 2:
        #    msg = _("Expected last and first name")
        #    raise ValidationError(msg)
        return self.cleaned_data['fio']

    def clean(self):
        cleaned_data = super(RegisterUserForm, self).clean()
        # check for matching passwords
        if 'password1' not in self.errors and 'password2' not in self.errors:
            if cleaned_data['password1'] != cleaned_data['password2']:
                msg = _("Passwords do not match")
                raise ValidationError(msg)
        return cleaned_data

    def _parce_fio_to_fullname(self, user, fio):
        if len(fio) > 0:
            user.first_name = fio

    def save(self, request=None, commit=True):
        do_activation = edw_settings.REGISTRATION_PROCESS['do_activation']
        self.instance.recognize_as_registered()
        self.instance.user.is_active = do_activation
        self.instance.user.email = self.cleaned_data['email']
        self.instance.user.set_password(self.cleaned_data['password1'])
        self._parce_fio_to_fullname(self.instance.user, self.cleaned_data['fio'])
        customer = super(RegisterUserForm, self).save(commit)
        password = self.cleaned_data['password1']
        if self.cleaned_data['preset_password']:
            self._send_password(request, customer.user, password)
        if do_activation:
            user = authenticate(username=customer.user.username, password=password)
            login(request, user)
        else:
            self._send_activation_email(request, customer.user)
            logout(request)

        customer_registered.send_robust(sender=self.__class__, customer=customer, request=request)

        msg = _("A customer ‘{email}’ success registered.\n"
                "To complete the registration, click the link that was sent to you by e-mail")
        return msg.format(**self.cleaned_data)

    def _send_password(self, request, user, password):
        current_site = get_current_site(request)
        context = Context({
            'site_name': current_site.name,
            'absolute_base_uri': request.build_absolute_uri('/'),
            'password': password,
            'user': user,
        })
        subject = select_template([
            '{}/email/register-user-subject.txt'.format(edw_settings.APP_LABEL),
            'edw/email/register-user-subject.txt',
        ]).render(context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = select_template([
            '{}/email/register-user-body.txt'.format(edw_settings.APP_LABEL),
            'edw/email/register-user-body.txt',
        ]).render(context)
        user.email_user(subject, body)

    def _send_activation_email(self, request, user):
        """
        Send the activation email. The activation key is simply the
        username, signed using TimestampSigner.
        """
        current_site = get_current_site(request)
        activation_key = signing.dumps(
            obj=getattr(user, user.USERNAME_FIELD),
            salt=edw_settings.REGISTRATION_PROCESS['registration_salt']
        )
        activation_link = request.build_absolute_uri(reverse('registration_activate', kwargs={'activation_key': activation_key}))
        context = Context({
            'site_name': current_site.name,
            'activation_link': activation_link,
            'expiration_days': edw_settings.REGISTRATION_PROCESS['account_activation_days'],
            'user': user,
        })
        subject = select_template([
            '{}/email/activate-account-subject.txt'.format(edw_settings.APP_LABEL),
            'edw/email/activate-account-subject.txt',
        ]).render(context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = select_template([
            '{}/email/activate-account-body.txt'.format(edw_settings.APP_LABEL),
            'edw/email/activate-account-body.txt',
        ]).render(context)
        user.email_user(subject, body)


#class ContinueAsGuestForm(ModelForm):
#    """
#    Handles Customer's decision to order as guest.
#    """
#    form_name = 'continue_as_guest_form'
#
#    class Meta:
#        model = CustomerModel
#        fields = ()  # this form doesn't show any fields
#
#    def save(self, request=None, commit=True):
#        self.instance.recognize_as_guest()
#        self.instance.user.is_active = edw_settings.GUEST_IS_ACTIVE_USER
#        if self.instance.user.is_active:
#            # set a usable password, otherwise the user later can not reset its password
#            password = get_user_model().objects.make_random_password(length=30)
#            self.instance.user.set_password(password)
#        return super(ContinueAsGuestForm, self).save(commit)