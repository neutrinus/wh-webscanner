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
from logs import log
from settings   import apath



class PluginDomainExpireDate(PluginMixin):
    '''
    This Plugin uses whois data to determine domain expiration date
    '''
    tlds = []
    def __init__(self):
        try: 
            # load tlds, ignore comments and empty lines:
            #https://mxr.mozilla.org/mozilla/source/netwerk/dns/src/effective_tld_names.dat?raw=1
            with open(apath("effective_tld_names.dat.txt)") as tldFile:
                self.tlds = [line.strip() for line in tldFile if line[0] not in "/\n"]
        except IOError:
            log.error("Could not find file effective_tld_names.dat.txt")

    #http://stackoverflow.com/questions/1066933/how-to-extract-domain-name-from-url/1069780#1069780
    def getDomain(self,url, tlds):
        urlElements = urlparse(url)[1].split('.')
        # urlElements = ["abcde","co","uk"]

        for i in range(-len(urlElements),0):
            lastIElements = urlElements[i:]
            #    i=-3: ["abcde","co","uk"]
            #    i=-2: ["co","uk"]
            #    i=-1: ["uk"] etc

            candidate = ".".join(lastIElements) # abcde.co.uk, co.uk, uk
            wildcardCandidate = ".".join(["*"]+lastIElements[1:]) # *.co.uk, *.uk, *
            exceptionCandidate = "!"+candidate

            # match tlds: 
            if (exceptionCandidate in tlds):
                return ".".join(urlElements[i:]) 
            if (candidate in tlds or wildcardCandidate in tlds):
                return ".".join(urlElements[i-1:])
                # returns "abcde.co.uk"
        raise ValueError("Domain not in global list of TLDs")

    
    name = unicode(_("Check domain expiration date"))
    wait_for_download = False
    
    def run(self, command):
        domain = self.getDomain(command.test.url,self.tlds)
        log.debug("Checking whois data for %s"%(domain))
        
        try:
            data = pywhois.whois(domain)   
            
            if hasattr(data,'expiration_date') and (len(data.expiration_date) >0): 
                output = data.expiration_date[0]
                
                try: 
                    domainexp = self.cast_date(output)
                    # convert time.struct_time object into a datetime.datetime
                    dt = date.fromtimestamp(mktime(domainexp))
                    
                    from scanner.models import Results
                    res = Results(test=command.test, group = RESULT_GROUP.general, importance=5)

                    res.output_desc = unicode(_("Domain expiration date") )
                    if dt - date.today() > timedelta(days=20):
                        res.output_full = unicode(_("<p>Your domain will be valid till %s. There is still %s days to renew it.</p>"%(dt, (dt - date.today()).days )) )
                        res.status = RESULT_STATUS.success
                    else:
                        res.output_full = unicode(_("<p>Better renew your domain, its valid till %s! There is only %s days left.</p>"%(dt, (dt - date.today()).days ) ))
                        res.status = RESULT_STATUS.error
                    
                    res.output_full += unicode(_("<p> We use <a href='http://en.wikipedia.org/wiki/Whois'>WHOIS</a> data to check domain expiration date. Depending on your domain registrar this date may be inaccurate or outdated.</p> "))
                    
                    res.save()
                except StandardError,e:
                    log.exception("output:%s exception:%s "%(str(output),str(e)) )
                    return STATUS.exception
                 
                    
                return res.status
            else:  
                log.debug("This gTLD doesnt provide valid domain expiration date in whois database")
                return STATUS.exception
        except ValueError,e:
            log.exception("%s"%str(e))
            return STATUS.exception
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



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
            '%d-%b-%Y %H:%M:%S',        # 30-Mar-2012 15:32:20
            '%Y-%m-%d %H:%M:%S %Z',    # 2012-04-28 15:22:46 GMT
        ]

        for format in known_formats:
            try:
                return time.strptime(date_str.strip(), format)
            except ValueError, e:
                pass # Wrong format, keep trying
        
        raise NameError("Unsupported date format: " + str(date_str))
        return None

