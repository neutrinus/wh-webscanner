# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

#from .forms import EmailRegistrationInlineForm

urlpatterns = patterns('',
    # override django.contrib.auth.urls for logout
    url(r'^logout/$', 'account.views.logout', name='logout'),

    # this two webscanner url packs override default flow (must be before
    # registration and registration_email
    url(r'^', include('registration.backends.webscanner_inline.urls')),
    url(r'^', include('registration.backends.webscanner.urls')),
    url(r'^', include('registration_email.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),


)

