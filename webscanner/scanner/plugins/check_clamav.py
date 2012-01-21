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
from scanner.models import STATUS,RESULT_STATUS
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


class PluginClamav(PluginMixin):
    name = unicode(_('Clamscan'))
    
    def run(self, command):
        domain = command.test.domain

        tmppath = PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(12))
        
        
        try:
            log.debug(unicode(_("Downloading webpage")))
            # Download webpage
            #command = PATH_WGET + " -P "+ tmppath + " -t 2 -T 15 -Q 30M -r -q -l 2 -np http://" + domain + ":" + utest_opt.port + utest_opt.path
            #command = PATH_WGET + " -P %s -o wget.log -t 1 -T 10 -Q 30m -r -l 0 -np http://%s"%(str(tmppath),str(domain))
            cmd = PATH_WGET + " -U wh-webscanner -xd -xg  -r+ -l 2 -P %s %s"%(str(tmppath),str(domain))
            
            args = shlex.split(cmd)
            p = subprocess.Popen(args,  stdout=subprocess.PIPE)
            (stdoutdata, stderrdata) = p.communicate()

            log.debug(unicode(_("Webpage downloaded, run clamscan")))
            
            #scan website
            cmd = PATH_CLAMSCAN + " "+ tmppath 
            args = shlex.split(cmd)
            p2 = subprocess.Popen(args, stdout=subprocess.PIPE)          
            (output, stderrdata2) = p2.communicate()

            log.debug(unicode(_("Clamscan finished")))

            numberofthreats = int(re.search('Infected files: (?P<kaczka>[0-9]*)',output).group('kaczka'))

            
            
            from scanner.models import Results
            res = Results(test=command.test)
            res.output_desc = unicode(_("Antivirus check"))
            
            if numberofthreats > 0:
                
                res.status = RESULT_STATUS.error
                res.output_full = unicode(_("Our antivirus found <b>%s</b> infected files on your website"%(numberofthreats)))

            else:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("Our antivirus claims that there is no infected files on your website."))
            
            res.save()
            
            
          
            
            #as plugin finished - its success
            return STATUS.success
        except Exception,e:
            log.exception(_("No check can be done: %s "%(e)))
            return STATUS.exception
    



if __name__ == '__main__':
    main()
