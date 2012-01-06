# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

scannerpatterns = patterns('',
        url(r'^/?$', 'scanner.views.index'),
        url(r'^results/?$', 'scanner.views.results'),
        
)

