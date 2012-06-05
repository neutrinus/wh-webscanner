# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
#from webscanner.scanner.views import *

urlpatterns = patterns('account.views',
        url(r'^user/logout/?$', 'ulogout'),
)



