#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
#http://code.google.com/p/pywhois/ 
import random
import HTMLParser
import urllib
import sys
import urlparse
import random
import string
import re
import shlex, subprocess
from time import sleep
from datetime import date
from plugin import PluginMixin
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


#PATH_KASPERSKY = '/opt/kaspersky/kav4fs/bin/kav4fs-control'
PATH_CLAMSCAN = '/home/marek/projekty/guardier/guardier-scanner/tools/fake_kaspersky_clean.sh'
PATH_WGET = '/usr/bin/wget'
PATH_TMPSCAN = '/tmp/'


class PluginClamav(PluginMixin):
    name = unicode(_('AntiVirus Scanner'))
    description = unicode(_('Check website for viruses and malware using CLAMAV antivirus software'))

    def make_test(self, command):
        
        domain = str(current_test.users_test.domain.url)
        tmppath = PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(12))
        
        
        try:
            # Download webpage
            #command = PATH_WGET + " -P "+ tmppath + " -t 2 -T 15 -Q 30M -r -q -l 2 -np http://" + domain + ":" + utest_opt.port + utest_opt.path
            command = PATH_WGET + " -P "+ tmppath + " -t 2 -T 15 -Q 30M -r -q -l 2 -np http://" + domain 
            args = shlex.split(command)
            p = subprocess.Popen(args,  stdout=subprocess.PIPE)
            (stdoutdata, stderrdata) = p.communicate()
            
            #scan website
            command = PATH_KASPERSKY + " --scan-file "+ tmppath 
            args = shlex.split(command)
            p2 = subprocess.Popen(args, stdout=subprocess.PIPE)          
            (output, stderrdata2) = p2.communicate()

            #from scanner.models import Results
            #res = Results(test=command.test)
            #res.output_desc = unicode(_("http return code"))
           
            #if (int(httpstatus) > 199) & (int(httpstatus) < 399) :
                #res.output_full = unicode(_("Server returned <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - it safe"%(unicode(httpstatus),httplib.responses[int(httpstatus)] ) ))
                #res.status = RESULT_STATUS.success
            #else:
                #res.output_full = unicode(_("Server returned unsafe <a href='http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'>\"%s %s\"</a> code - please check it"%(unicode(httpstatus),httplib.responses[int(httpstatus)]) ))
                #res.status = RESULT_STATUS.error
            #res.save()

            
            #as plugin finished - its success
            return STATUS.success
        except Exception,e:
            log.exception(_("No check can be done: %s "%(e)))
            return STATUS.exception
    



    #def results(self,current_test, notify_type, language_code):
        #try:          
            #output = current_test.output
            #numberofthreats = int(re.search('Threats found:.+ (?P<kaczka>[0-9]*)',output).group('kaczka'))
            
            #if numberofthreats > 0:
                #return (STATUS.unsuccess,_('Some threats found on your website'))
            #else:
                #return (STATUS.success,_('Not threats found - website is clean'))

        #except Exception,e:
            #return (STATUS.exception,"Exception: " + str(e))


if __name__ == '__main__':
    main()
