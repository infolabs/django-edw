# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import patterns
from django.utils.module_loading import import_string

from edw.views.auth import AuthFormsView
from edw.views.auth import LoginView
from edw.views.auth import LogoutView
from edw.views.auth import PasswordResetView
from edw.views.auth import PasswordChangeView
from edw.views.auth import ActivationView
from edw.forms.auth import RegisterUserForm as DefaultRegisterUserForm


register_user_form_class_path = getattr(
    settings, 'REGISTER_USER_FORM_CLASS', None
)
if register_user_form_class_path:
    RegisterUserForm = import_string(register_user_form_class_path)
else:
    RegisterUserForm = DefaultRegisterUserForm


urlpatterns = patterns(
    '',
    url(r'^password/reset/$', PasswordResetView.as_view(),
        name='password-reset'),
    url(r'^login/$', LoginView.as_view(),
        name='login'),
    url(r'^register/$', AuthFormsView.as_view(form_class=RegisterUserForm),
        name='register-user'),
    url(r'^activate/(?P<activation_key>[-:\w]+)/$', ActivationView.as_view(),
        name='registration_activate'),
    #url(r'^continue/$', AuthFormsView.as_view(form_class=ContinueAsGuestForm),
    #    name='continue-as-guest'),
    url(r'^logout/$', LogoutView.as_view(),
        name='logout'),
    url(r'^password/change/$', PasswordChangeView.as_view(),
        name='password-change'),
)
