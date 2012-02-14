#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#based on http://maestric.com/doc/python/recursive_w3c_html_validator
import sys
import os
import random
import HTMLParser
import urllib
import sys
import urlparse
import string
import re
import shlex


from time import sleep
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from settings import SCREENSHOT_SIZE, STATIC_ROOT
from selenium import webdriver
from pyvirtualdisplay import Display

from logs import log



#http://pypi.python.org/pypi/selenium        
#http://code.google.com/p/fighting-layout-bugs/
#http://code.google.com/p/webpagetest/source/browse/#svn%2Ftrunk%2Fagent%2Fbrowser%2Ffirefox
#https://developers.google.com/pagespeed/#url=guardier.com&mobile=false&rule=MinifyHTML    


class PluginMakeScreenshotFirefox(PluginMixin):    
    name = unicode(_('Screenshot in Firefox'))
    wait_for_download = False
    
    def run(self, command):
        domain = command.test.url
        from scanner.models import Results
       
        try:
            filename = 'screenshots/' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) + ".png"
            display = Display(visible=0,size=SCREENSHOT_SIZE)
            display.start()
            log.debug("VDispaly started: %s "%(str(display)))

            browser = webdriver.Firefox()
            log.debug("Firefox started: %s "%(str(browser)))
            browser.get(domain)
            sleep(random.uniform(2,5))
            browser.save_screenshot(STATIC_ROOT+"/"+filename)

            res = Results(test=command.test)
            res.group = RESULT_GROUP.screenshot
            res.status = RESULT_STATUS.info
            res.output_desc = unicode(_("Firefox")) 
            res.output_full = '<a href="/static/%s"><img src="/static/%s" width="300px" title="%s (version:%s)" /></a>'%(filename,filename,"Firefox",browser.capabilities['version']
            )
            res.save()

            browser.close()           
            display.sendstop()
            
            log.debug("Saving screenshot (result:%s)) in: %s "%(res.pk,STATIC_ROOT+"/"+filename))
            #there was no exception - test finished with success
            return STATUS.success
        except Exception,e:
            log.exception("Error while creating screenshot: %s "%(e))
            return STATUS.exception

