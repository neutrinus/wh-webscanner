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


#PATH_KASPERSKY = '/opt/kaspersky/kav4fs/bin/kav4fs-control'
PATH_KASPERSKY = '/home/marek/projekty/guardier/guardier-scanner/tools/fake_kaspersky_clean.sh'
PATH_WGET = '/usr/bin/wget'
PATH_TMPSCAN = '/tmp/'


class PluginKaspersky(PluginMixin):
    name = unicode(_('Virus Scanner'))
    description = unicode(_('Check website for viruses and malware using kaspersky antivirus software'))
    frequencies = (
        ('5',    _('every 5 minutes') ),
        ('60',   _('every hour')),
        ('1440', _('once a day') ),
        ('10080', _('once a week')),
    )

    def make_test(self, current_test, timeout=None):
        

        utest_opt = current_test.users_test.users_test_options
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

            current_test.output = output
            current_test.save()

            (status,kaczka) = self.results(current_test,None , None)
            return status,output
            #return (STATUS.success, str(stdoutdata2) )

        except Exception,e:
            return (STATUS.exception,"Exception: " + str(e))
    



    def results(self,current_test, notify_type, language_code):
        try:          
            output = current_test.output
            numberofthreats = int(re.search('Threats found:.+ (?P<kaczka>[0-9]*)',output).group('kaczka'))
            
            if numberofthreats > 0:
                return (STATUS.unsuccess,_('Some threats found on your website'))
            else:
                return (STATUS.success,_('Not threats found - website is clean'))

        except Exception,e:
            return (STATUS.exception,"Exception: " + str(e))


if __name__ == '__main__':
    main()