#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
#http://code.google.com/p/pywhois/ 
import random
import HTMLParser
import urllib
import urlparse
import random
import string
import re
import shlex, subprocess
from time import sleep
from datetime import date
from plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
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


#PATH_KASPERSKY = '/'
PATH_CLAMSCAN = '/usr/bin/clamscan'
PATH_WGET = '/usr/bin/puf'
PATH_TMPSCAN = '/tmp/clamdd/'


class PluginOptipng(PluginMixin):
    name = unicode(_('OptiPNG'))
    
    def run(self, command):
        domain = command.test.domain
        
        
        #find -type f -iname "*.png" -exec optipng   -o3 {} \;
        
        
        #try:           
            ##scan website
            #cmd = PATH_CLAMSCAN + " "+ command.test.download_path
            #args = shlex.split(cmd)
            #p = subprocess.Popen(args, stdout=subprocess.PIPE)          
            #(output, stderrdata2) = p.communicate()
            #if p.returncode != 0:
                #log.exception("%s returned non-0 status, stderr: %s "%(PATH_CLAMSCAN,stderrdata2))    
                #return STATUS.exception
                
            #numberofthreats = int(re.search('Infected files: (?P<kaczka>[0-9]*)',output).group('kaczka'))
            
            #from scanner.models import Results
            #res = Results(test=command.test)
            #res.group = RESULT_GROUP.security
            #res.output_desc = unicode(_("Antivirus check"))
            
            #if numberofthreats > 0:
                #res.status = RESULT_STATUS.error
                #res.output_full = unicode(_("Our antivirus found <b>%s</b> infected files on your website"%(numberofthreats)))
            #else:
                #res.status = RESULT_STATUS.success
                #res.output_full = unicode(_("Our antivirus claims that there is no infected files on your website."))           
            #res.save()
            
            

            
            ##as plugin finished - its success
            #return STATUS.success
        #except Exception,e:
            #log.exception("No check can be done: %s "%(e))
            #return STATUS.exception
    



if __name__ == '__main__':
    main()
