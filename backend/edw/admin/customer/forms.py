# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _


#==============================================================================
# CustomerCreationForm
#==============================================================================
class CustomerCreationForm(UserCreationForm):
    class Meta(UserChangeForm.Meta):
        model = get_user_model()

    def save(self, commit=True):
        self.instance.is_staff = True
        return super(CustomerCreationForm, self).save(commit=False)


#==============================================================================
# CustomerChangeForm
#==============================================================================
class CustomerChangeForm(UserChangeForm):
    email = forms.EmailField(required=False)

    class Meta(UserChangeForm.Meta):
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        initial['email'] = instance.email or ''
        super(CustomerChangeForm, self).__init__(initial=initial, *args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email').strip()
        if not email:
            # nullify empty email field in order to prevent unique index collisions
            return None

        if get_user_model().objects.filter(email=email).exists():
            msg = _("A customer with the e-mail address ‘{email}’ already exists.")
            raise forms.ValidationError(msg.format(email=email))

        return email

    def save(self, commit=False):
        self.instance.email = self.cleaned_data['email']
        return super(CustomerChangeForm, self).save(commit)
