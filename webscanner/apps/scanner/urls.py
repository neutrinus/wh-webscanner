# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
#from webscanner.scanner.views import *

urlpatterns = patterns('scanner.views',
        url(r'^/?$', 'index', name='scanner_index'),
        url(r'^terms/?$', 'terms', name='scanner_terms'),
        url(r'^about/?$', 'about', name='scanner_about'),
        url(r'^tariffs/?$', 'pricing', name='scanner_pricing'),
        url(r'^results/?$', 'results'),
        url(r'^user/scan_archive/?$', 'scan_archive', name='scanner_scan_archive'),
        url(r'^check_results/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?$', 'check_results'),
        url(r'^reports/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/$', 'show_report', name='scanner_report'),
        url(r'^simplereports/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/$', 'show_simple_report', name='scanner_simple_report'),
)

