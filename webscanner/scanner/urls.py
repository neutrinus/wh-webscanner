# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

scannerpatterns = patterns('',
        url(r'^/?$', 'scanner.views.index'),
        url(r'^results/?$', 'scanner.views.results'),
        url(r'^check_new_results/?$', 'scanner.views.check_new_results'),
        url(r'^scan_progress/?$', 'scanner.views.scan_progress'),
        
)


