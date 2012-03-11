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

class PluginMakeScreenshots(PluginMixin):
    name = unicode(_('Screenshots'))
    wait_for_download = False
    
    def run(self, command):
        url = command.test.url
        from scanner.models import Results

        display = Display(visible=0,size=SCREENSHOT_SIZE)
        display.start()
        log.debug("VDisplay started: %s "%(str(display)))
        jscode = ""
        timing = {}
        
        browsernames = ["firefox", "chrome"]
        
        jscode += "var browsernames = [ "
        for browsername in browsernames:
            jscode += '"%s",'%(browsername)
        jscode += "]; \n"
        
        for browsername in browsernames:
            filename = 'screenshots/' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) + ".png"

            if browsername == "firefox":
                browser = webdriver.Firefox()
            if browsername == "chrome":
                browser = webdriver.Chrome()
                
            sleep(1)
            log.debug("Browser %s started: %s "%(browsername, str(browser)))
            browser.get(url)
            
            #give a bit time for loading async-js
            sleep(3)
            browser.save_screenshot(MEDIA_ROOT+"/"+filename)
            timing[browsername] = browser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")
            #build javascript table with timing values
            jscode += "var timingdata_%s = [ "%(browsername)
            for time in ["navigationStart","domainLookupStart","domainLookupEnd","connectStart","requestStart", "domLoading","domInteractive","domComplete","loadEventEnd"]:
                jscode += "['%s',%s ],"%(time, timing[browsername][time]-timing[browsername]["navigationStart"])
            jscode += "]; \n"
            
            res = Results(test=command.test, group=RESULT_GROUP.screenshot, status=RESULT_STATUS.info, output_desc = browsername )
            res.output_full = '<a href="/media/%s"><img src="/media/%s" width="300px" title="%s (version:%s)" /></a>'%(filename,filename,browsername,browser.capabilities['version']
            )
            res.save()
            log.debug("Saving screenshot (result:%s)) in: %s "%(res.pk,MEDIA_ROOT+"/"+filename))
            browser.quit()
           

            

        res = Results(test=command.test, group = RESULT_GROUP.general, status = RESULT_STATUS.success)
        res.output_desc = unicode(_("Webpage load time")) 
        res.output_full = unicode(_("<p>We measure how long it takes to load webpage in our test webbrowser. Bellow you can find measured timing of <a href='https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html'>events</a> for your webpage.  Fast webpages have loadtime bellow 4000 milisecs, very slow more than 12000 milisecs.</p>")) 
        
        res.output_full += "<div id='timing_plot' style='height:400px;width:580px;'></div><script>\n"
                
        jscode += "var timing_plot =  jQuery.jqplot('timing_plot', ["
        for browsername in browsernames:
            jscode += "timingdata_%s,"%(browsername)
        jscode += "],    \
            {   \
            title: 'Loadtime - events', \
            axesDefaults: { \
                tickRenderer: $.jqplot.CanvasAxisTickRenderer , \
                tickOptions: { \
                angle: -70, \
                fontSize: '10pt' \
                } \
            }, \
            legend: { show:true, location: 'w', labels: browsernames}, \
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
            
            
        loadtime=0
        for browsername in browsernames:
            tmp =  timing[browsername]["loadEventEnd"]-timing[browsername]["navigationStart"]
            if tmp > loadtime:
                loadtime = tmp
            
        res.output_full += jscode
        res.output_full += "<p>Loading your website took <b>%s</b> milisecs (at maximum).</p>"%(loadtime)
        if loadtime > 5000:
            res.status = RESULT_STATUS.warning
        if loadtime > 15000:
            res.status = RESULT_STATUS.error
        res.save()

        
        
        display.sendstop()
        

        #there was no exception - test finished with success
        return STATUS.success
