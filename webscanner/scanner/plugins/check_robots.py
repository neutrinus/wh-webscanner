#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#based on http://maestric.com/doc/python/recursive_w3c_html_validator
import sys
import os
import random
import urllib2
import sys
import urlparse
import re
import cgi
from time import sleep
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from logs import log


class PluginCheckRobots(PluginMixin):

    name = unicode(_('Check robots.txt'))
    wait_for_download = False

    def run(self, command):
        robotsurl = urlparse.urlparse(command.test.url).scheme + "://" + urlparse.urlparse(command.test.url).netloc +"/robots.txt"
        log.debug("Looking for: %s "%(robotsurl))

        try:
            from scanner.models import Results
            res = Results(test=command.test, group = RESULT_GROUP.general,importance=2)

            res.output_desc = unicode(_("robots.txt"))
            res.output_full = '<p><a href="http://www.robotstxt.org/">robots.txt</a> file is used to control automatic software (like Web Wanderers, Crawlers, or Spiders). Address of your robots.txt for your domain should be: <code>%s</code> </p> '%(robotsurl)
            res.status = RESULT_STATUS.success
            output = ""
            try:
                req = urllib2.Request(robotsurl)
                req.add_header('Referer', 'http://webcheck.me/')
                result = urllib2.urlopen(req)

                linecounter=0
                for line in result.readlines():
                    linecounter += 1

                    #comments
                    if re.match(r'^(\s)?#.*',line):
                        continue
                    #empty lines
                    if re.match(r'^(\s)+',line):
                        continue

                    if re.match(r'^\s*(user-agent)|(disallow)|(allow)|(sitemap)|(crawl-delay)|(noarchive)|(noindex)|(nofollow)|(nopreview)|(nosnippet)|(index):\s.*',line.lower()):
                        output +=  "%s<br />"%(line)
                    else:
                        res.output_full += '<p>There was an error while parsing your robots.txt: <b>bad syntax</b> in line %s:<code>%s</code> </p>'%(linecounter,cgi.escape(line))
                        res.status = RESULT_STATUS.error
                        break
                else:
                    res.output_full += '<p>robots.txt is present:<code>%s</code></p>'%(output)

            except urllib2.HTTPError, e:
                res.status = RESULT_STATUS.warning
                res.output_full += '<p>There was no robots.txt. HTTP code was:%s.</p>'%(e.code)
            except urllib2.URLError, e:
                res.status = RESULT_STATUS.warning
                res.output_full += '<p>There was problem while connecting to server:%s.</p>'%(e.reason)

            res.save()

            #there was no exception - test finished with success
            return STATUS.success
        except Exception,e:
            log.exception(_("No validation can be done: %s "%(e)))
            return STATUS.exception

