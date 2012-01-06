#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import httplib
from time import sleep
from urlparse import urlparse
from plugin import PluginMixin
from scanner.models import STATUS
#from scanner.models import UsersTest_Options

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

class PluginCheckHTTPCode(PluginMixin):
    name = unicode(_('Check HTTP site response'))
    description = unicode(_('Check http server http code response'))

    def run(self, test):
        
        
        
        try:
            conn = httplib.HTTPConnection(test.domain,80)
            conn.request("HEAD", "/")        
            a = conn.getresponse()
            output =  str(a.status)
            
            current_test.output = output
            current_test.save()
            
            (status,kaczka) = self.results(current_test,None , None)
            return status,output
            
        except Exception,e:
            print _("No validation can be done: ") + str(e)
            return (STATUS.exception,"Exception: " + str(e))


    def results(self,current_test, notify_type, language_code):  
        output = current_test.output


        if not output:
            return (STATUS.exception, _("Error: Empty output provided "))
    
        
        if not (output.isdigit()):
            return (STATUS.unsuccess, _("Error: Non numerical output code ") + output)


        if (int(output) > 199) & (int(output) < 399) :
            if notify_type == NOTIFY_TYPES.email:
                return (STATUS.success,_("Server returned ") + unicode(output) + " code - it safe." )
            
            #if notify_type == NOTIFY_TYPES.phone:
                #return (STATUS.success,_("Server returned ") + unicode(output) + "." )
            

            return (STATUS.success,_("Server returned <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>") + unicode(output) + "</a> code - it safe" )
        else:
            if notify_type == NOTIFY_TYPES.email:
                return (STATUS.unsuccess,_("Server returned unsafe ") + unicode(output) + " code - please check it" )
                
            #if notify_type == NOTIFY_TYPES.phone:
                #return (STATUS.unsuccess,_("Server returned unsafe ") + unicode(output) + "." )                  
                
            return (STATUS.unsuccess, _("Server returned  unsafe <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>") + unicode(output) + "</a> code - please check it" )
           
      
	        	
if __name__ == '__main__':
    main()
