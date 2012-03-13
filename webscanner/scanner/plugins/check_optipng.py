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
from settings import PATH_OPTIPNG
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _


from logs import log

class PluginOptipng(PluginMixin):
    name = unicode(_('OptiPNG'))
    
    def run(self, command):
        domain = command.test.domain
       
        command.test.download_path = "/tmp/webscanner/FA2SW0LQF8H2GXUQ4LNYPZ3F"
        cmd = "find %s -type f -iname '*.png' -exec %s -o3 {} \; "%(command.test.download_path,PATH_OPTIPNG )
        args = shlex.split(cmd)
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        (output, stderrdata2) = p.communicate()
        if p.returncode != 0:
            log.exception("%s returned non-0 status, stderr: %s "%(PATH_CLAMSCAN,stderrdata2))
            return STATUS.exception
        

        #** Processing: /tmp/webscanner/FA2SW0LQF8H2GXUQ4LNYPZ3F/png/plik.png
        #Output IDAT size = 534 bytes (29665 bytes decrease)
        #Output file size = 715 bytes (29688 bytes = 97.65% decrease)

        olines = output.split("\n")
        for oline in olines:
            if re.match('\*\* Processing: .*',oline):
                print "DUUUPA"
                
            if re.match('^Output IDAT size = .*',oline):
                print "DUUUPAK"

            if re.match('^Output file size = .*',oline):
                print "DUUUPAKJ"
                
            print oline
            
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
        
        #as plugin finished - its success
        return STATUS.success



if __name__ == '__main__':
    main()
