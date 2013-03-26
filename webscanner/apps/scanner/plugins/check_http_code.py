#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import time
import httplib
from time import sleep
from urlparse import urlparse
from plugin import PluginMixin

#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from urlparse import urlparse


#http://wiki.openstreetmap.org/wiki/OpenLayers_Simple_Example

class PluginCheckHTTPCode(PluginMixin):

    name = unicode(_('Check HTTP site response'))
    description = unicode(_('Check http server http code response'))
    wait_for_download = False

    def run(self, command):
        conn = httplib.HTTPConnection(command.test.domain(),command.test.port())
        conn.request("HEAD", "/",body="",headers={  'Accept-Encoding': 'gzip,deflate,bzip2,exi',
                                                    'Referer': 'http://webcheck.me/',
                                                    })
        response = conn.getresponse()
        httpstatus =  str(response.status)


        if not httpstatus:
            self.log.exception(_("Error: Empty httpstatus provided "))
            return STATUS.exception

        if not (httpstatus.isdigit()):
            self.log.exception(_("Error: Non numerical httpstatus code "))
            return STATUS.unsuccess

        if command.test.check_performance:
            #check http encoding aceptation
            from scanner.models import Results

            encoding = response.getheader("Content-Encoding")
            res = Results(test=command.test, group = RESULT_GROUP.performance, importance=1)
            res.output_desc = unicode(_("HTTP compression"))
            if encoding:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("<p>Server agreed to compress http data using %s method.</p>"%(unicode(encoding) ) ))
            else:
                res.status = RESULT_STATUS.warning
                res.output_full = unicode(_("<p>Server did not agree to compress http data using any method. HTTP compression can lower your site traffic volume and speed up page loading.</p>" ))

            headers = ""
            for header in response.getheaders():
                (a,b) = header
                headers += "%s: %s <br>"%(a,b)

            res.output_full += unicode(_("<p>There are different types of compression available, <a href='http://en.wikipedia.org/wiki/HTTP_compression'>wikipedia article</a> covers this subject sufficiently. Headers sent by your webserver: <code>%s</code> </p> "%(headers )))
            res.save()

        #there was no exception - test finished with success
        return STATUS.success

