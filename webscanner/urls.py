# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
import registration
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += patterns('django.views.generic.simple',)
urlpatterns += patterns('',   (r'^', include('scanner.urls')), )
urlpatterns += patterns('',   (r'^', include('account.urls')), )
urlpatterns += patterns('',   (r'^', include('payments.urls')), )
urlpatterns += patterns('',   (r'^', include('addonsapp.urls')), )
urlpatterns += patterns('',   (r'^user/', include('registration.urls')), )

from django.conf.urls.static import static
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


