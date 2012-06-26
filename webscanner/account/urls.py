# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('account.views',
        url(r'^user/logout/?$', 'ulogout'),
)



