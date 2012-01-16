#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import time
import httplib
from time import sleep
from urlparse import urlparse
from plugin import PluginMixin
#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS
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

    def check_encoding(domain, encoding):
        conn = httplib.HTTPConnection(domain,80)
        conn.request("HEAD", "/",body="",headers={'Accept-Encoding': encoding})
        a = conn.getresponse()
        httpstatus =  str(a.status)
        
    
    
    def run(self, command):
        time.sleep(1)
        
       
        try:
            conn = httplib.HTTPConnection(command.test.domain,80)
            conn.request("HEAD", "/",body="",headers={'Accept-Encoding': 'gzip,deflate,bzip2,exi'})  
            response = conn.getresponse()
            httpstatus =  str(response.status)
            
            
            if not httpstatus:
                log.exception(_("Error: Empty httpstatus provided "))
                return STATUS.exception
        
            if not (httpstatus.isdigit()):
                log.exception(_("Error: Non numerical httpstatus code "))
                return STATUS.unsuccess

            #check http_status 200>X>300
            from scanner.models import Results
            res = Results(test=command.test)
            res.output_desc = unicode(_("http return code"))
           
            if (int(httpstatus) > 199) & (int(httpstatus) < 399) :
                res.output_full = unicode(_("Server returned <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - it safe"%(unicode(httpstatus),httplib.responses[int(httpstatus)] ) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("Server returned unsafe <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - please check it"%(unicode(httpstatus),httplib.responses[int(httpstatus)]) ))
                res.status = RESULT_STATUS.error
            res.save()
            
            
            #check http encoding aceptation
            encoding = response.getheader("Content-Encoding")

            res = Results(test=command.test)
            
            res.output_desc = unicode(_("http compresion"))
            if encoding:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("Server agreed to compress http data using %s method."%(unicode(encoding) ) ))
            else:
                res.status = RESULT_STATUS.warning
                res.output_full = unicode(_("Server didnt agree to compress http data using any method. HTTP compression can lower your site traffic volume and speedup page loading." ))                
            res.save()
            
            #there was no exception - test finished with success
            return STATUS.success

        except Exception,e:
            log.exception(_("No validation can be done: %s "%(e)))
            return STATUS.exception
      
	        	
#if __name__ == '__main__':
    #main()
