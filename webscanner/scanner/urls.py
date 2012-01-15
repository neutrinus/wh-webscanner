# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from webscanner.scanner.views import *

scannerpatterns = patterns('',
        url(r'^/?$', index),
        url(r'^results/?$', results),
        url(r'^check_results/?$', check_new_results, name="scanner.views.check_results"),
        url(r'^check_new_results/(?P<last_date>\w+)/?$', check_new_results),
        url(r'^scan_progress/?$', scan_progress),

)


