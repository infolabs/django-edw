# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.conf.urls import url, patterns, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse

from . import api
from . import views

from rest_framework import routers


class SharedAPIRootRouter():
    router = routers.DefaultRouter()

    def register(self, *args, **kwargs):
        self.router.register(*args, **kwargs)


router = SharedAPIRootRouter()
router.register(r'todos', api.TodoViewSet)


def render_robots(request):
    permission = 'noindex' in settings.ROBOTS_META_TAGS and 'Disallow' or 'Allow'
    return HttpResponse('User-Agent: *\n%s: /\n' % permission, content_type='text/plain')


i18n_urls = (
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns = patterns('',
    url(r'^robots\.txt$', render_robots),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^api/', include(SharedAPIRootRouter.router.urls)),
    url(r'^edw/', include('edw.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^jsreverse/$', 'django_js_reverse.views.urls_js', name='js_reverse'),
    url(r'^$', views.index, name='index'),
    #url(r'^todo/(?P<slug>[0-9A-Za-z_.-]+)/$', TodoDetailView.as_view(), name="todo_detail"),
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
