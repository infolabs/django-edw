# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseRedirect
from django.utils.functional import SimpleLazyObject
from django.utils import timezone
from edw.models.customer import CustomerModel
from edw import settings as edw_settings

def get_customer(request, force=False):
    if force or not hasattr(request, '_cached_customer'):
        request._cached_customer = CustomerModel.objects.get_from_request(request)
    return request._cached_customer


class CustomerMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        response = self.process_response(request, response)
        return response

    def process_request(self, request):
        assert hasattr(request, 'session'), "The django-edw middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        assert hasattr(request, 'user'), "The django-edw middleware requires an authentication middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.auth.middleware.AuthenticationMiddleware'."
        request.customer = SimpleLazyObject(lambda: get_customer(request))

    def process_response(self, request, response):
        content_type = response.get('content-type')
        try:
            if content_type.startswith('text/html'):
                # only update last_access when rendering the main page
                request.customer.last_access = timezone.now()
                request.customer.save(update_fields=['last_access'])
                if response.status_code == 401:
                    return HttpResponseRedirect(f'{edw_settings.UNAUTHORIZED_LOGIN_URL}?next={request.get_full_path()}')
        except AttributeError:
            pass
        return response
