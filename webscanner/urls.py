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
    #url(r'^payments/',include('gpayments.urls')),
)


urlpatterns += patterns('django.views.generic.simple',
    #url(r'^/?$','redirect_to',{'url':'/user/welcome/'}),
    #url(r'^/user/?$','redirect_to',{'url':'/user/welcome/'}),
)
urlpatterns += patterns('',   (r'^', include('scanner.urls')), )
urlpatterns += patterns('',   (r'^', include('account.urls')), )
urlpatterns += patterns('',   (r'^user/', include('registration.urls')), )

#from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static                                      
# it works only when debug
#urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)  

   
