#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#based on http://maestric.com/doc/python/recursive_w3c_html_validator

import sys
import os
import random
import HTMLParser
import urllib
import sys
import urlparse
from time import sleep

w3c_validator = 'http://validator.w3.org/'

from plugin import PluginMixin
from scanner.models import STATUS,NOTIFY_TYPES

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

class PluginCheckW3CValid(PluginMixin):
    
    frequencies = (
        ('5',    _('every 5 minute') ),
        ('60',   _('every hour')),
        ('1440', _('once a day') ),
        ('10080', _('once a week')),
    )
    name = unicode(_('W3C Validator'))
    description = unicode(_('Check wheter site is in w3c code'))

    def make_test(self, current_test, timeout=None):
        domain = current_test.users_test.domain.url
        utest_opt = current_test.users_test.users_test_options
        url = domain + ":" + utest_opt.port + utest_opt.path
        
        try:
            result = urllib.urlopen(w3c_validator + 'check?uri=' + domain)
           
            output = "status:" + str(result.info().getheader('x-w3c-validator-status')) + ", warnings: "  + str(result.info().getheader('x-w3c-validator-warnings')) + ", errors:" + str(result.info().getheader('x-w3c-validator-errors'))  
            
            if result.info().getheader('x-w3c-validator-status') == 'Valid' :
                status = STATUS.success
            else:
                status = STATUS.unsuccess
            
            return(status,output)        
        except StandardError,e:
            print "No validation can be done: " + str(e)
            return (STATUS.exception,str(e))

    def results(self,current_test, notify_type, language_code):
        
        if notify_type:
            output = current_test.output + ".."
        else:
            output = '<a href="' + w3c_validator + 'check?uri=' + \
            unicode(current_test.users_test.domain) + '">' + current_test.output + '</a>'
        
        return current_test.status,output
