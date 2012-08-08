#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import httplib
from urlparse import urlparse
from plugin import PluginMixin
#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from scanner import pywhois
import random
import HTMLParser
import urllib
import sys
import time
import json
from time import sleep

from logs import log

class PluginGoogleSite(PluginMixin):
    '''
    This Plugin uses google API:
    https://developers.google.com/web-search/docs/reference
    to ask for data related to website (number of backlinks, keywords)
    '''

    name = unicode(_("Google Backlinks checker"))
    wait_for_download = False

    def run(self, command):
        domain = command.test.url

        query = urllib.urlencode({'q' : 'link:%s'%(domain)})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&hl=en&%s'%(query)
        search_results = urllib.urlopen(url)
        jdata = json.loads(search_results.read())

        if 'estimatedResultCount' not in jdata['responseData']['cursor']:
            log.debug("no estimatedResultCount")
            return STATUS.exception

        from scanner.models import Results
        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)
        res.output_desc = unicode(_("google backlinks ") )
        res.output_full = unicode(_('<p>There is about %(number_of_sites)s sites linking to your site. <a href="%(url)s">See them!</a></p> <p><small>This data is provided by google and may be inaccurate.</small></p> ' % {
            "number_of_sites":  jdata['responseData']['cursor']['estimatedResultCount'],
            "url": jdata['responseData']['cursor']['moreResultsUrl']
        }))
        res.status = RESULT_STATUS.info
        res.save()

        #there was no exception - test finished with success
        return STATUS.success
