#! /usr/bin/env python
# -*- encoding: utf-8 -*-
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
import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 


class PluginDomainExpireDate(PluginMixin):
    name = unicode(_("Check domain expiration date"))
    description = unicode(_("Check domain expiration date using data from whois database"))
    wait_for_download = False
    
    def run(self, command):
        domain = command.test.domain

        #time.sleep(1)
        try:
            data = pywhois.whois(domain)   
            
            if hasattr(data,'expiration_date'):
                output = data.expiration_date[0]
                
                try: 
                    domainexp = self.cast_date(output)
                    # convert time.struct_time object into a datetime.datetime
                    dt = date.fromtimestamp(mktime(domainexp))
                    
                    from scanner.models import Results
                    res = Results(test=command.test)
                    res.group = RESULT_GROUP.general

                    res.output_desc = unicode(_("Domain expiration date") )
                    if dt - date.today() > timedelta(days=29):
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
                log.exception(_(unicode(_("Error: This gTLD doesnt provide valid domain expiration date in whois database"))))
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
