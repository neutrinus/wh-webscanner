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
from settings import SCREENSHOT_SIZE, MEDIA_ROOT
from selenium import webdriver
from pyvirtualdisplay import Display

from logs import log



#http://pypi.python.org/pypi/selenium        


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
            log.debug("VDisplay started: %s "%(str(display)))

            browser = webdriver.Firefox()
            log.debug("Firefox started: %s "%(str(browser)))
            browser.get(domain)
            sleep(random.uniform(2,5))
            browser.save_screenshot(MEDIA_ROOT+"/"+filename)

            res = Results(test=command.test)
            res.group = RESULT_GROUP.screenshot
            res.status = RESULT_STATUS.info
            res.output_desc = unicode(_("Firefox")) 
            res.output_full = '<a href="/media/%s"><img src="/media/%s" width="300px" title="%s (version:%s)" /></a>'%(filename,filename,"Firefox",browser.capabilities['version']
            )
            res.save()

            browser.close()      
            sleep(2)
            display.sendstop()
            
            log.debug("Saving screenshot (result:%s)) in: %s "%(res.pk,MEDIA_ROOT+"/"+filename))
            #there was no exception - test finished with success
            return STATUS.success
        except Exception,e:
            log.exception("Error while creating screenshot: %s "%(e))
            return STATUS.exception

