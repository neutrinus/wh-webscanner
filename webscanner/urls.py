# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/', include('account.urls')),
    url(r'^', include('scanner.urls')),
    url(r'^', include('payments.urls')),
    url(r'^', include('addonsapp.urls')),
)
#urlpatterns += patterns('',   (r'^account/', include('captcha.backends.default.urls')), )


from django.conf.urls.static import static
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


