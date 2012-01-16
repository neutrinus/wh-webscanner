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
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

w3c_validator = 'http://validator.w3.org/'

import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 


class PluginCheckW3CValid(PluginMixin):
    
    name = unicode(_('W3C Validator'))
    description = unicode(_('Check wheter site is in w3c code'))

    def run(self, command):
        domain = command.test.domain
        
        try:
            checklink = w3c_validator + 'check?uri=' + domain
            result = urllib.urlopen(checklink)
           
            output = "status: %s, warnings: %s, errors: %s."%(
                    str(result.info().getheader('x-w3c-validator-status')),
                    str(result.info().getheader('x-w3c-validator-warnings')),
                    str(result.info().getheader('x-w3c-validator-errors')))
            
            from scanner.models import Results
            res = Results(test=command.test)

            if result.info().getheader('x-w3c-validator-status') == 'Valid' :
                res.status = RESULT_STATUS.success
                res.output_desc = "W3C Validator marks your website as Valid. " + output + ' <a href="%s">Check details at W3C</a>'%checklink 
            else:
                res.status = RESULT_STATUS.warning
                res.output_desc = "W3C Validator marks your website as Invalid. " + output + ' <a href="%s">Check details at W3C</a>'%checklink 
            res.save()
            
            #there was no exception - test finished with success
            return STATUS.success
        except Exception,e:
            log.exception(_("No validation can be done: %s "%(e)))
            return STATUS.exception

    #def results(self,current_test, notify_type, language_code):
        
        #if notify_type:
            #output = current_test.output + ".."
        #else:
            #output = '<a href="' + w3c_validator + 'check?uri=' + \
            #unicode(current_test.users_test.domain) + '">' + current_test.output + '</a>'
        
        #return current_test.status,output
