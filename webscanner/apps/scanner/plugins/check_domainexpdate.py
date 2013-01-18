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
from scanner import pywhois
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
from urlparse import urlparse
from settings   import apath
from addonsapp.tools import extract_domain


class PluginDomainExpireDate(PluginMixin):
    '''
    This Plugin uses whois data to determine domain expiration date and domain age
    '''
    name = unicode(_("Check domain expiration date"))
    wait_for_download = False

    def run(self, command):
        domain = extract_domain(command.test.url)
        self.log.debug("Checking whois data for %s"%(domain))
        from scanner.models import Results

        data = pywhois.whois(domain)

        if hasattr(data,'expiration_date') and (len(data.expiration_date) >0):
            domainexp = self.cast_date(data.expiration_date[0])
            # convert time.struct_time object into a datetime.datetime
            dt = date.fromtimestamp(mktime(domainexp))

            res = Results(test=command.test, group = RESULT_GROUP.general, importance=5)

            res.output_desc = unicode(_("Domain expiration date") )
            if dt - date.today() > timedelta(days=20):
                res.output_full = unicode(_("<p>Your domain will be valid until %(date)s. There is still %(days)s days to renew it.</p>"% {"date":dt,
                                    "days":(dt - date.today()).days
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

        if hasattr(data,'creation_date') and (len(data.creation_date) >0):
            domain_creation = self.cast_date(data.creation_date[0])
            # convert time.struct_time object into a datetime.datetime
            dt = date.fromtimestamp(mktime(domain_creation))

            res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)

            res.output_desc = unicode(_("Domain age") )
            res.output_full = unicode(_("<p>Your domain has been first registred %(days)s days ago (registration date: %(date)s).</p>"% {"date":dt,
                                    "days":(date.today() - dt).days
                                    }))
            if date.today() - dt < timedelta(days=500):
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

    def cast_date(self,date_str):
        """Convert any date string found in WHOIS to a time object.
        """
        known_formats = [
            '%d-%b-%Y',                 # 02-jan-2000
            '%Y-%m-%d',                 # 2000-01-02
            '%Y.%m.%d',                 # 2000.01.02
            '%d-%b-%Y %H:%M:%S %Z',     # 24-Jul-2009 13:20:03 UTC
            '%a %b %d %H:%M:%S %Z %Y',  # Tue Jun 21 23:59:59 GMT 2011
            '%Y-%m-%dT%H:%M:%SZ',       # 2007-01-26T19:10:31Z
            '%Y-%m-%d %H:%M:%S',        # 2007-01-26 19:10:31
            '%d-%b-%Y %H:%M:%S',        # 30-Mar-2012 15:32:20
            '%Y-%m-%d %H:%M:%S %Z',     # 2012-04-28 15:22:46 GMT
            '%Y.%m.%d %H:%M:%S',        # 2012.04.28 15:22:46
        ]

        for format in known_formats:
            try:
                return time.strptime(date_str.strip(), format)
            except ValueError, e:
                pass # Wrong format, keep trying

        raise NameError("Unsupported date format: " + str(date_str))
        return None

