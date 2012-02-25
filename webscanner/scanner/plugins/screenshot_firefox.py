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
#https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html

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

            timing = browser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")
            
            res = Results(test=command.test)
            res.group = RESULT_GROUP.screenshot
            res.status = RESULT_STATUS.info
            res.output_desc = unicode(_("Firefox")) 
            res.output_full = '<a href="/media/%s"><img src="/media/%s" width="300px" title="%s (version:%s)" /></a>'%(filename,filename,"Firefox",browser.capabilities['version']
            )
            res.save()

            res = Results(test=command.test)
            res.group = RESULT_GROUP.general
            res.status = RESULT_STATUS.success
            res.output_desc = unicode(_("Webpage load time")) 
            res.output_full = unicode(_("<p>We measure how long it takes to load webpage in our test webbrowser. Bellow you can find measured timing of <a href='https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html'>events</a> for your webpage.  Fast webpages have loadtime bellow 4000 milisecs, very slow more than 12000 milisecs.</p>")) 
            
            jscode = "<div id='timing_plot' style='height:400px;width:580px;'></div><script> \
var tdata = [ "

            for time in ["navigationStart","domainLookupStart","domainLookupEnd","connectStart","requestStart", "domLoading","domInteractive","domComplete","loadEventEnd"]:
                jscode += "['%s',%s ],"%(time, timing[time]-timing["navigationStart"])
            
            jscode += "]; \n  \
    var timing_plot = jQuery.jqplot('timing_plot', [tdata],    \
    {   \
    title: 'Loadtime - events', \
    axesDefaults: { \
        tickRenderer: $.jqplot.CanvasAxisTickRenderer , \
        tickOptions: { \
          angle: -70, \
          fontSize: '10pt' \
        } \
    }, \
    axes: { \
      xaxis: { \
        renderer: $.jqplot.CategoryAxisRenderer, \
      }, \
      yaxis: { \
        pad: 0, \
        label: 'time [milisecs]', \
      } \
    }, \
    }); \
    </script> \
    "
    
            loadtime = timing["loadEventEnd"]-timing["navigationStart"]
            res.output_full += jscode
            res.output_full += "<p>Loading your website took <b>%s</b> milisecs.<p>"%(loadtime)
            if loadtime > 4000:
                res.status = RESULT_STATUS.warning
            if loadtime > 12000:
                res.status = RESULT_STATUS.error
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

