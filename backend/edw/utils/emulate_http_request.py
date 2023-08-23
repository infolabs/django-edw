# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves.urllib.parse import urlparse

from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.http.request import HttpRequest


class EmulateHttpRequest(HttpRequest):
    default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"
    default_language = "ru"
    default_remote_ip = "95.71.9.164"
    default_method = "GET"

    def current_site(self, is_secure):
        site = get_current_site(None)
        if is_secure:
            return "https://{0}".format(site)

        return "http://{0}".format(site)

    """
    Use this class to emulate a HttpRequest object, when templates must be rendered
    asynchronously, for instance when an email must be generated out of an Notification object.
    """
    def __init__(self, customer, stored_request, is_secure=True):
        super(EmulateHttpRequest, self).__init__()
        absolute_base_uri = stored_request.get('absolute_base_uri', None)
        if absolute_base_uri is None:
            absolute_base_uri = self.current_site(is_secure)
        parsedurl = urlparse(absolute_base_uri)
        self.path = self.path_info = parsedurl.path
        self.environ = {}
        self.META['PATH_INFO'] = parsedurl.path
        self.META['SCRIPT_NAME'] = ''
        self.META['HTTP_HOST'] = parsedurl.netloc
        self.META['HTTP_X_FORWARDED_PROTO'] = parsedurl.scheme
        self.META['QUERY_STRING'] = parsedurl.query
        self.META['HTTP_USER_AGENT'] = stored_request.get('user_agent', self.default_user_agent)
        self.META['REMOTE_ADDR'] = stored_request.get('remote_ip', self.default_remote_ip)
        self.method = stored_request.get('method', self.default_method)
        self.LANGUAGE_CODE = self.COOKIES['django_language'] = stored_request.get('language', self.default_language)
        self.customer = customer
        if customer is not None:
            self.user = customer.is_anonymous() and AnonymousUser or customer.user
        else:
            self.user = AnonymousUser()

