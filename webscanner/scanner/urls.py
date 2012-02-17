# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from webscanner.scanner.views import *

scannerpatterns = patterns('',
        url(r'^/?$', index),
        url(r'^results/?$', results),
        url(r'^check_results/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?$', check_results),
        url(r'^scan_progress/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?$', scan_progress),
        url(r'^reports/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?$', show_report),

)




