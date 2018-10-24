# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import logout, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from rest_auth.views import (
    LoginView as OriginalLoginView,
    PasswordChangeView as OriginalPasswordChangeView
)

from edw import settings as edw_settings
from edw.models.customer import CustomerModel
from edw.rest.serializers.auth import PasswordResetSerializer, PasswordResetConfirmSerializer
from edw.signals.auth import user_activated


class AuthFormsView(GenericAPIView):
    """
    Generic view to handle authetication related forms such as user registration
    """
    serializer_class = None
    form_class = None

    def post(self, request, *args, **kwargs):
        if request.customer.is_visitor():
            (request.customer, is_created) = CustomerModel.objects.get_or_create_from_request(request)
        else:
            is_created = False
        data = request.data.copy()
        form = self.form_class(data=data, instance=request.customer)
        if form.is_valid():
            msg = form.save(request=request)
            return Response(
                {'success': msg},
                status=status.HTTP_200_OK
            )
        if is_created:
            request.customer.delete()
        return Response(
            dict(form.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class GetTokenView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            email = request.customer.user.email
            try:
                token, created = Token.objects.get_or_create(user=request.user)
            except ValueError as e:
                return Response(
                    {'detail': _('User is not recognized as "registered"')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"email": email, "key": token.key},
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {'detail': _("Logged out")},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(OriginalLoginView):
    def login(self):
        """
        Logs in as the given user
        """
        dead_user = None if self.request.user.is_anonymous() or self.request.customer.is_registered() else self.request.customer.user
        super(LoginView, self).login()  # this rotates the session_key
        if dead_user and dead_user.is_active is False:
            dead_user.delete()  # to keep the database clean


class LogoutView(APIView):
    """
    Calls Django logout method and delete the auth Token assigned to the current User object.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            import re
            http_authorization = request.META.get('HTTP_AUTHORIZATION', None)
            if http_authorization is not None:
                if re.search('Token ', http_authorization):
                    request.user.auth_token.delete()
        except:
            pass
        logout(request)
        request.user = AnonymousUser()
        return Response(
            {'success': _("Successfully logged out.")},
            status=status.HTTP_200_OK
        )

class PasswordResetView(GenericAPIView):
    """
    Calls Django Auth PasswordResetForm save method.

    Accepts the following POST parameters: email
    Returns the success/fail message.
    """
    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        email = request.data.__getitem__('email')
        User = get_user_model()
        user = User.objects.filter(
            email__iexact=email,
            is_active=False
        )
        if user.count() > 0:
            user = user[0]
            user.email_user(_('Password reset'), _('For reset password you need first activation your account'))

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        # Return the success message with OK HTTP status
        msg = _("Instructions on how to reset the password have been sent to '{email}'.")
        return Response(
            {'success': msg.format(**serializer.data)},
            status=status.HTTP_200_OK
        )


try:
    from django.utils.http import urlsafe_base64_decode as uid_decoder
except:
    # make compatible with django 1.5
    from django.utils.http import base36_to_int as uid_decoder


class PasswordResetConfirmView(GenericAPIView):
    """
    Password reset e-mail link points onto this view, which when invoked by a GET request renderes
    a HTML page containing a password reset form. This form then can be used to reset the user's
    password using a RESTful POST request.

    Since the URL for this view is part in the email's body text, expose it to the URL patterns as:

    ```
    url(r'^password-reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    ```

    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.
    """
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)
    template_name = 'edw/auth/password-reset-confirm.html'
    token_generator = default_token_generator

    def get(self, request, uidb64=None, token=None):
        data = {'uid': uidb64, 'token': token}
        serializer_class = self.get_serializer_class()
        password = 'x' * serializer_class._declared_fields['new_password1']._kwargs.get('min_length', 3)
        data.update(new_password1=password, new_password2=password)
        serializer = serializer_class(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response({'validlink': False})
        return Response({'validlink': True, 'user_name': force_text(serializer.user)})

    def post(self, request, uidb64=None, token=None):
        data = {'uid': uidb64,
                'token': token,
                'new_password1': request.data['new_password1'],
                'new_password2': request.data['new_password2']
                }
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response({"success": _("Password has been reset with the new password.")})


class PasswordChangeView(OriginalPasswordChangeView):

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response({"success": _("New password has been saved.")})


class ActivationView(APIView):
    """
    Base class for user activation views.
    """
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)
    template_name = '{}/auth/account-activate.html'.format(edw_settings.APP_LABEL)

    def get(self, request, *args, **kwargs):
        """
        The base activation logic; subclasses should leave this method
        alone and implement activate(), which is called from this
        method.
        """
        activated_user = self.activate(request, *args, **kwargs)
        if not activated_user:
            return Response({
                'is_activate': False,
                'message': _("Error validate account. Validate link wrong or expired validate code.")
            })
        else:
            #user = authenticate(username=customer.user.username, password=password)
            #login(request, user)
            return Response({
                'is_activate': True,
                'message': _("Account success validate.")
            })

    def validate_key(self, activation_key):
        """
        Verify that the activation key is valid and within the
        permitted activation time window, returning the username if
        valid or ``None`` if not.
        """
        try:
            username = signing.loads(
                activation_key,
                salt=edw_settings.REGISTRATION_PROCESS['registration_salt'],
                max_age=edw_settings.REGISTRATION_PROCESS['account_activation_days'] * 86400
            )
            return username
        # SignatureExpired is a subclass of BadSignature, so this will
        # catch either one.
        except signing.BadSignature:
            return None

    def get_user(self, username):
        """
        Given the verified username, look up and return the
        corresponding user account if it exists, or ``None`` if it
        doesn't.
        """
        User = get_user_model()
        lookup_kwargs = {
            User.USERNAME_FIELD: username,
            'is_active': False
        }
        try:
            user = User.objects.get(**lookup_kwargs)
            return user
        except User.DoesNotExist:
            return None

    def activate(self, request, *args, **kwargs):
        # This is safe even if, somehow, there's no activation key,
        # because unsign() will raise BadSignature rather than
        # TypeError on a value of None.
        username = self.validate_key(kwargs.get('activation_key'))
        if username is not None:
            user = self.get_user(username)
            if user is not None:
                user.is_active = True
                user.save()
                user_activated.send_robust(sender=self.__class__, user=user, request=request)
                return user
        return False
