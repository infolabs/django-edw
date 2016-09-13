# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import patterns, url
from edw.forms.auth import RegisterUserForm, ContinueAsGuestForm
from edw.views.auth import AuthFormsView, LoginView, LogoutView, PasswordResetView, PasswordChangeView, ActivationView


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
    url(r'^continue/$', AuthFormsView.as_view(form_class=ContinueAsGuestForm),
        name='continue-as-guest'),
    url(r'^logout/$', LogoutView.as_view(),
        name='logout'),
    url(r'^password/change/$', PasswordChangeView.as_view(),
        name='password-change'),
)
