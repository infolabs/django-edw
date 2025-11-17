from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from edw.settings import NAME_MAX_LENGTH
USERNAME_FIELD_HELP_TEXT = _(
    'Required field. Length must not exceed 30 characters. Only letters, digits and symbols @/./+/-/_ are accepted.'
)
USERNAME_LENGTH_VALIDATION_TEXT = _('Username length must not exceed 30 characters.')


# ==============================================================================
# CustomerCreationForm
# ==============================================================================
class CustomerCreationForm(UserCreationForm):
    class Meta(UserChangeForm.Meta):
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = USERNAME_FIELD_HELP_TEXT

    def clean(self):
        if 'username' in self.cleaned_data:
            username = self.cleaned_data['username']
            if username and len(username) > NAME_MAX_LENGTH:
                raise forms.ValidationError(USERNAME_LENGTH_VALIDATION_TEXT)

    def save(self, commit=True):
        self.instance.is_staff = True
        return super(CustomerCreationForm, self).save(commit=False)


# ==============================================================================
# CustomerChangeForm
# ==============================================================================
class CustomerChangeForm(UserChangeForm):
    email = forms.EmailField(required=False)

    class Meta(UserChangeForm.Meta):
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        initial['email'] = instance.email or ''
        super(CustomerChangeForm, self).__init__(initial=initial, *args, **kwargs)
        self.fields['username'].help_text = USERNAME_FIELD_HELP_TEXT

    def clean(self):
        if 'username' in self.cleaned_data:
            username = self.cleaned_data['username']
            if username and len(username) > 30:
                raise forms.ValidationError(USERNAME_LENGTH_VALIDATION_TEXT)

    def clean_email(self):
        email = self.cleaned_data.get('email').strip()
        if not email:
            # nullify empty email field in order to prevent unique index collisions
            return None
        customers = get_user_model().objects.filter(email=email)
        if len(customers) and (len(customers) > 1 or self.instance != customers[0]):
            msg = _("A customer with the e-mail address ‘{email}’ already exists.")
            raise forms.ValidationError(msg.format(email=email))

        return email

    def save(self, commit=False):
        self.instance.email = self.cleaned_data['email']
        return super(CustomerChangeForm, self).save(commit)
