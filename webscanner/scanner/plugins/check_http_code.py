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
from scanner.models import STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _


import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 

class PluginCheckHTTPCode(PluginMixin):
    
    name = unicode(_('Check HTTP site response'))
    description = unicode(_('Check http server http code response'))

    def run(self, command):
       
        
       
        try:
            conn = httplib.HTTPConnection(command.test.domain,80)
            conn.request("HEAD", "/")        
            a = conn.getresponse()
            output =  str(a.status)
            
            
            if not output:
                log.exception(_("Error: Empty output provided "))
                return STATUS.exception
        
            if not (output.isdigit()):
                log.exception(_("Error: Non numerical output code "))
                return STATUS.unsuccess

            from scanner.models import Results
            res = Results(test=command.test)
            res.status = STATUS.success
            
            
            if (int(output) > 199) & (int(output) < 399) :
                res.output_desc = unicode(_("Server returned <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'> %s </a> code - it safe"%unicode(output) ))
                res.status = STATUS.success
                
            else:
                res.output_desc = unicode(_("Server returned unsafe <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'> %s </a> code - please check it"%unicode(output) ))
                res.status = STATUS.unsuccess
                
            res.save()
            return res.status
                
            
        except Exception,e:
            log.exception(_("No validation can be done: %s "%(e)))
            return STATUS.exception
      
	        	
#if __name__ == '__main__':
    #main()
