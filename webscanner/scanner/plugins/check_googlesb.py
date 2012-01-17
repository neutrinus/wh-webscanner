#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import httplib
from urlparse import urlparse
from plugin import PluginMixin
#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from scanner import pywhois
import random
import HTMLParser
import urllib
import sys
import time
from time import sleep
import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 

sburl = '/safebrowsing/api/lookup?client=webscanner&apikey=ABQIAAAAcHK-fy7eQw0ew14dgrixiRTuuUEoCbs4nG8IiJX3yqHHfBuDtw&appver=0.1&pver=3.0&url='
# my key: ABQIAAAAcHK-fy7eQw0ew14dgrixiRTuuUEoCbs4nG8IiJX3yqHHfBuDtw

class PluginGoogleSafeBrowsing(PluginMixin):
    name = unicode(_("Google Safe Browsing Blacklist checker"))
    description = unicode(_("Check if domain is listed in google safe browsing blacklist"))
    
    def run(self, command):
        domain = command.test.domain

        #time.sleep(1)
        try:
            conn = httplib.HTTPSConnection("sb-ssl.google.com")
            conn.request("GET", sburl+domain)  
            response = conn.getresponse()
            httpstatus =  str(response.status)
            httpbody = str(response.read())
                      
            from scanner.models import Results
            res = Results(test=command.test)                    
            res.output_desc = unicode(_("Google Safe Browssing Blacklist") )

            message = '<p>For more information please visit following sites: www.antiphishing.org, StopBadware.org. <a href="http://code.google.com/apis/safebrowsing/safebrowsing_faq.html#whyAdvisory">Advisory provided by Google</a></p>'
            
            if (int(httpstatus) == 204):
                res.output_full = unicode(_('Your domain is not listed at Google Safe Browsing Blacklist <a href="http://www.google.com/safebrowsing/diagnostic?site=http://%s">Check it at google</a>. It means that probably there is no malware or phishing. '%command.test.domain) + message) 
                res.status = RESULT_STATUS.success
                
            elif (int(httpstatus) == 200):
                res.output_full = unicode(_('Your domain is listed at Google Safe Browsing Blacklist because of %s <a href="http://www.google.com/safebrowsing/diagnostic?site=http://%s">Check it at google</a>. Please check your website because its possible that there is %s.'%(command.test.domain,httpbody,httpbody) ) + message) 
                res.status = RESULT_STATUS.error
            else:
                log.exception("Google sent non expected http code:%s body:%s "%(httpcode,httpbody) )
                return STATUS.exception
            
            res.save()

            #there was no exception - test finished with success
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



    def cast_date(self,date_str):
        """Convert any date string found in WHOIS to a time object.
        """
        known_formats = [
            '%d-%b-%Y',                 # 02-jan-2000
            '%Y-%m-%d',                 # 2000-01-02
            '%d-%b-%Y %H:%M:%S %Z',     # 24-Jul-2009 13:20:03 UTC
            '%a %b %d %H:%M:%S %Z %Y',  # Tue Jun 21 23:59:59 GMT 2011
            '%Y-%m-%dT%H:%M:%SZ',       # 2007-01-26T19:10:31Z
        ]

        for format in known_formats:
            try:
                return time.strptime(date_str.strip(), format)
            except ValueError, e:
                pass # Wrong format, keep trying
        
        raise NameError("Unsupported date format: " + str(date_str))
        return None


if __name__ == '__main__':
    main()
