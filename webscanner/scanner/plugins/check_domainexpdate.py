#! /usr/bin/env python
import sys
import os
#http://code.google.com/p/pywhois/ 
# -*- encoding: utf-8 -*-
import pywhois
import random
import HTMLParser
import urllib
import sys
import urlparse
import time
from time import sleep
from time import mktime
from datetime import date
from datetime import datetime
from datetime import timedelta
from plugin import PluginMixin
from scanner.models import STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

class PluginDomainExpireDate(PluginMixin):
    name = unicode(_("Check domain expiration date"))
    description = unicode(_("Check domain expiration date using data from whois database"))

    #dont do it to often - whois servers will ban you
    frequencies = (
        ('1440', _('once a day') ),
        ('10080', _('once per week')),
    )

    

    def make_test(self, current_test, timeout=None):
        domain = current_test.users_test.domain.url

        try:
            data = pywhois.whois(domain)   
            
            if hasattr(data,'expiration_date'):
                output = data.expiration_date[0]
            
                current_test.output = output
                current_test.save()
                
                (status,kaczka) = self.results(current_test,None , None)
                return status,output
            else:  
                return (STATUS.exception,unicode(_("Error: This gTLD doesnt provide valid domain expiration date in whois database")))
            
        except StandardError,e:
            print "error: " + str(e)
            return (STATUS.exception,"Exception: " + str(e))


    def results(self,current_test, notify_type, language_code):
        
        if not current_test.output:
            return (STATUS.exception,_("Error: This gTLD doesnt provide valid domain expiration date in whois database"))
            
        try: 
            domainexp = self.cast_date(current_test.output)
            # convert time.struct_time object into a datetime.datetime
            dt = date.fromtimestamp(mktime(domainexp))
            

            if dt - date.today() > timedelta(days=29):
                return (STATUS.success, _("Your domain will be walid for at least 20 days") )
            else:
                return (STATUS.unsuccess,_("Better renew your domain!") )
        except StandardError,e:
            return (STATUS.exception,str(current_test.output) + " " + str(e))
            #print >>sys.stdout, str(datetime.now()) + " Error: " + str(e)
            
            
        return None



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
