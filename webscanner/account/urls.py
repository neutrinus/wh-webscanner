# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

#from .forms import EmailRegistrationInlineForm

urlpatterns = patterns('',
    # override django.contrib.auth.urls for logout
    url(r'^logout/$', 'account.views.logout', name='logout'),

    url(r'^', include('account.registration.backends.inline.urls')),
    url(r'^', include('registration_email.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),


)

