# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, patterns, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from edw.views.auth import PasswordResetConfirm
from edw.search.views import SearchView
from edw.search.serializers import ProductSearchSerializer


def render_robots(request):
    permission = 'noindex' in settings.ROBOTS_META_TAGS and 'Disallow' or 'Allow'
    return HttpResponse('User-Agent: *\n%s: /\n' % permission, content_type='text/plain')

        
i18n_urls = (
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns = patterns('',
    url(r'^robots\.txt$', render_robots),
    url(r'^edw/', include('edw.urls', namespace='edw')),
)


if settings.USE_I18N:
    urlpatterns += i18n_patterns('', *i18n_urls)
else:
    urlpatterns += i18n_urls

if settings.DEBUG:
    urlpatterns = patterns('',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'', include('django.contrib.staticfiles.urls')),
) + urlpatterns
