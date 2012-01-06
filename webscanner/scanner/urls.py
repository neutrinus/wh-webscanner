# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^/', 'scanner.views.index', name='index'),

)

