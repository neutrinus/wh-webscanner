#! /usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import with_statement
import sys
import os
import random
import httplib
from time import sleep
from urlparse import urlparse
from plugin import PluginMixin
#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
import whois
import random
import HTMLParser
import urllib
import sys
import time
from time import sleep
from time import mktime
from datetime import date
from datetime import datetime
from datetime import timedelta

from webscanner.utils.http import extract_domain


class PluginDomainExpireDate(PluginMixin):
    '''
    This Plugin uses whois data to determine domain expiration date and domain age
    '''
    name = unicode(_("Check domain expiration date"))
    wait_for_download = False

    def run(self, command):
        domain = str(extract_domain(command.test.url))
        self.log.debug("Checking whois data for %s"%(domain))
        from scanner.models import Results

        # works also when subdomain is added
        data = whois.query(domain)

        if data and data.expiration_date:
            dt = domainexp = data.expiration_date

            res = Results(test=command.test, group = RESULT_GROUP.general, importance=5)

            res.output_desc = unicode(_("Domain expiration date") )
            if dt.date() - date.today() > timedelta(days=20):
                res.output_full = unicode(_("<p>Your domain will be valid until %(date)s. There is still %(days)s days to renew it.</p>"% {"date":dt,
                                    "days":(dt.date() - date.today()).days
                                    }))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Better renew your domain, its valid until %(date)s! There is only %(days)s days left.</p>"% { "date" :dt,
                                    "days": (dt - date.today()).days } ))
                res.status = RESULT_STATUS.error

            res.output_full += unicode(_("<p class='muted'> We use <a href='http://en.wikipedia.org/wiki/Whois'>WHOIS</a> data to check domain expiration date. Depending on your domain registration operator this date may be inaccurate or outdated.</p> "))
            res.save()
        else:
            self.log.debug("This gTLD doesnt provide valid domain expiration date in whois database")

        if data and data.creation_date:
            dt = domain_creation = data.creation_date

            res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)

            res.output_desc = unicode(_("Domain age") )
            res.output_full = unicode(_("<p>Your domain has been first registred %(days)s days ago (registration date: %(date)s).</p>"% {"date":dt,
                                    "days":(date.today() - dt.date()).days
                                    }))
            if date.today() - dt.date() < timedelta(days=500):
                res.output_full += unicode(_("<p><b>Your domain is a fresh one. </b></p>"))
                res.status = RESULT_STATUS.warning
            else:
                res.output_full += unicode(_("<p><b>Good, your domain has a long history.</b></p>"))
                res.status = RESULT_STATUS.success

            res.output_full += unicode(_("<p>Domain age matters to a certain extent and newer domains generally struggle to get indexed and rank high in search results for their first few months (depending on other associated ranking factors). Consider buying a second-hand domain name or register domains way before using them.</p> "))
            res.output_full += unicode(_("<p class='muted' > We use <a href='http://en.wikipedia.org/wiki/Whois'>WHOIS</a> data to check domain creation date. Depending on your domain registration operator this date may be inaccurate or outdated.</p> "))
            res.save()
        else:
            self.log.debug("This gTLD doesnt provide valid domain creation date in whois database")

        return STATUS.success
