# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
import registration
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += patterns('',
    (r'^', include('scanner.urls')),
    (r'^', include('account.urls')),
    (r'^', include('payments.urls')),
    (r'^', include('addonsapp.urls')),
    (r'^user/', include('registration.urls')),
)
#urlpatterns += patterns('',   (r'^account/', include('captcha.backends.default.urls')), )


from django.conf.urls.static import static
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


