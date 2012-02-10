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
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from urlparse import urlparse
from logs import log



class PluginCheckHTTPCode(PluginMixin):
    
    name = unicode(_('Check HTTP site response'))
    description = unicode(_('Check http server http code response'))
    wait_for_download = False
    
    #def check_encoding(domain, encoding):
        #conn = httplib.HTTPConnection(domain,80)
        #conn.request("HEAD", "/",body="",headers={'Accept-Encoding': encoding})
        #a = conn.getresponse()
        #httpstatus =  str(a.status)
        
    
    
    def run(self, command):
       
        try:
            conn = httplib.HTTPConnection(command.test.domain(),command.test.port())
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
            res = Results(test=command.test, group = RESULT_GROUP.general, importance=5)
            res.output_desc = unicode(_("HTTP return code"))
           
            if (int(httpstatus) > 199) & (int(httpstatus) < 399) :
                res.output_full = unicode(_("<p>Server returned <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - it safe</p>"%(unicode(httpstatus),httplib.responses[int(httpstatus)] ) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Server returned unsafe <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - please check it</p>"%(unicode(httpstatus),httplib.responses[int(httpstatus)]) ))
                res.status = RESULT_STATUS.error
                
            res.output_full += unicode(_("<p>This is very low level check - it checks if webserver is reachable and answering</p> "))
                
            res.save()
            
            
            #check http encoding aceptation
            encoding = response.getheader("Content-Encoding")

            res = Results(test=command.test, group = RESULT_GROUP.general, importance=1)
            res.output_desc = unicode(_("HTTP compresion"))
            if encoding:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("<p>Server agreed to compress http data using %s method.</p>"%(unicode(encoding) ) ))
            else:
                res.status = RESULT_STATUS.warning
                res.output_full = unicode(_("<p>Server didnt agree to compress http data using any method. HTTP compression can lower your site traffic volume and speedup page loading.</p>" ))       
             
            headers = ""
            for header in response.getheaders():
               (a,b) = header
               headers += "%s: %s <br>"%(a,b)
               
            res.output_full += unicode(_("<p>There are different types of compression avalible, <a href='http://en.wikipedia.org/wiki/HTTP_compression>'>wikipedia article</a> covers this theme nicly. Headers sent by your webserver: <code>%s</code> </p> "%(headers )))
                
            res.save()
            
            #there was no exception - test finished with success
            return STATUS.success

        except Exception,e:
            log.exception(_("No validation can be done: %s "%(e)))
            return STATUS.exception
      
	        	
#if __name__ == '__main__':
    #main()
