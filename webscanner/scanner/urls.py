# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from webscanner.scanner.views import *

scannerpatterns = patterns('',
        url(r'^/?$', index),
        url(r'^results/?$', results),
        url(r'^check_results/?$', check_results),
        url(r'^scan_progress/?$', scan_progress),
)


