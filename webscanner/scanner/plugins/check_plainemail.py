#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import string
import re
from time import sleep
from datetime import date
from plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from logs import log


class PluginPlainTextEmail(PluginMixin):
    name = unicode(_('PlainTextEmails'))
    wait_for_download = True
    
    def run(self, command):
        path = command.test.download_path
        
        try:
            
            # We want to recurslivly grep all html files and look for something looking like email address
            filelist = []
            for root, dirs, files in os.walk(tmppath):
                for file in files:
                    filelist.append(root+file)
                        
            for file in filelist:
                print "analizing file: %s"%file
                memFile = open(file)
                for line in memFile.readlines():
                    match = re.search('MemTotal', line)    
                    if match is not None:
                        print match.group()                   
                memFile.close()
                
            from scanner.models import Results
            res = Results(test=command.test,group = RESULT_GROUP.security, importance=5)
            res.output_desc = unicode(_("Look for plain-text email addreses"))
            
            if numberofthreats > 0:
                res.status = RESULT_STATUS.warning
                res.output_full = unicode(_("Our antivirus found <b>%s</b> infected files on your website"%(numberofthreats)))
            else:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("Our antivirus claims that there is no infected files on your website."))           
            res.save()
            
            #as plugin finished - its success
            return STATUS.success
        except Exception,e:
            log.exception("No check can be done: %s "%(e))
            return STATUS.exception
    



if __name__ == '__main__':
    main()
