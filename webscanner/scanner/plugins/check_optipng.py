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
        path = command.test.download_path
        
        #command.test.download_path = "/tmp/webscanner/FA2SW0LQF8H2GXUQ4LNYPZ3F"
        
        cmd = "find %s -type f -iname '*.png' -exec %s -o3 {} \; "%(command.test.download_path,PATH_OPTIPNG )
        args = shlex.split(cmd)
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        (output, stderrdata2) = p.communicate()
        if p.returncode != 0:
            log.exception("%s returned non-0 status, stderr: %s "%(PATH_OPTIPNG,stderrdata2))
            return STATUS.exception

        #example output:
        #** Processing: /tmp/webscanner/FA2SW0LQF8H2GXUQ4LNYPZ3F/png/plik.png
        #Output IDAT size = 534 bytes (29665 bytes decrease)
        #Output file size = 715 bytes (29688 bytes = 97.65% decrease)

        txtoutput = ""
        fcounter = 0
        filename = ""

        olines = output.split("\n")
        for oline in olines:
            print oline
            re_filename =  re.search('\*\* Processing: (?P<filename>.*)',oline)
            if re_filename:
                filename = re_filename.group("filename")
                fcounter += 1
                pass

            re_size = re.search('^Output file size \= [0-9]+ bytes \((?P<oldsize>[0-9]+) bytes \= (?P<ratio>[0-9.]+)\% decrease\)$',oline)
            if re_size:
                oldsize = re_size.group("oldsize")
                ratio = re_size.group("ratio")
                txtoutput += "%s (%s bytes): <b>%s%%</b> <br />"%(filename[len(path)+1:], oldsize, ratio )
                        
        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.security,importance=2)
        res.output_desc = unicode(_("Images (png) optimalization"))
        
        if txtoutput:
            res.status = RESULT_STATUS.warning
            res.output_full = unicode(_("We analized %s files. Some of them may need optimalization: <code>%s</code>"%(fcounter,txtoutput)))
        else:
            res.status = RESULT_STATUS.success
            if fcounter >0:
                res.output_full = unicode(_("All %s png files looks optimized. Good!"%(fcounter)))
            else:
                res.status = RESULT_STATUS.info
                res.output_full = unicode(_("No png files found."))
        res.save()
        
        #as plugin finished - its success
        return STATUS.success

