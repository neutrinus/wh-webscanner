# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^user/logout/?$', 'account.views.ulogout'),
        url(r'^user/login/?$', 'django.contrib.auth.views.login'),
)




