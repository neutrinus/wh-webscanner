# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from webscanner.scanner.urls import scannerpatterns


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    #url(r'^payments/',include('gpayments.urls')),
)


urlpatterns += patterns('django.views.generic.simple',
    #url(r'^/?$','redirect_to',{'url':'/user/welcome/'}),
    #url(r'^/user/?$','redirect_to',{'url':'/user/welcome/'}),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# it works only when debug
urlpatterns += staticfiles_urlpatterns()
urlpatterns += scannerpatterns

