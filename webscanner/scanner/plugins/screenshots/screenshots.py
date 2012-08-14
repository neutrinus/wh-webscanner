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
import shutil
import signal
from time import sleep
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from settings import SCREENSHOT_SIZE, MEDIA_ROOT
from selenium import webdriver
from pyvirtualdisplay import Display
from PIL import Image

from scanner.plugins.optiimg import gentmpfilename, optimize_image
from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP

from logs import log


class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

def crop_screenshot(inputfile):
    img = Image.open(inputfile)
    box = (0, 0, 940, 400)
    area = img.crop(box)
    ofile = MEDIA_ROOT+"/screenshots/thumb_"+gentmpfilename()+".png"
    area.save(ofile, 'png')
    return(ofile)

#http://pypi.python.org/pypi/selenium
#https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html

class PluginMakeScreenshots(PluginMixin):
    '''
    This Plugin makes screenshots of a webpage by visiting it using different webbrowsers (firefox,chrome) and selenium.
    '''

    name = unicode(_('Screenshots'))
    wait_for_download = False

    def run(self, command):
        url = command.test.url
        from scanner.models import Results

        display = Display(visible=0,size=SCREENSHOT_SIZE)
        display.start()
        log.debug("VDisplay started: %s "%(str(display)))
        timing = {}
        max_loadtime = 0

        browsernames = ["firefox", "chrome"]

        for browsername in browsernames:
            filename = 'screenshots/' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) + ".png"

            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(3*60)  # 3 minutes

            try:
                if browsername == "firefox":
                    browser = webdriver.Firefox()
                if browsername == "chrome":
                    browser = webdriver.Chrome()

                log.debug("Browser %s started: %s "%(browsername, str(browser)))

                #http://seleniumhq.org/docs/04_webdriver_advanced.html
                browser.implicitly_wait(30)
                sleep(4)
                browser.get(url)

                #give a bit time for loading async-js
                sleep(3)
                browser.save_screenshot(MEDIA_ROOT+"/"+filename)
                thumb = crop_screenshot(MEDIA_ROOT+"/"+filename)

                #optimize snapshot
                screenshot = optimize_image(MEDIA_ROOT+"/"+filename, MEDIA_ROOT+"/screenshots/", True)
                screenshot_thumb = optimize_image(thumb, MEDIA_ROOT+"/screenshots/", True)

                timing_data = browser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")

                timing[browsername] = []

                for time in ["navigationStart","domainLookupStart","domainLookupEnd","connectStart","requestStart", "domLoading","domInteractive","domComplete","loadEventEnd"]:
                    timing[browsername].append( (time, timing_data[time] - timing_data["navigationStart"]))

                tmp_timing =  timing_data["loadEventEnd"] - timing_data["navigationStart"]
                if tmp_timing > max_loadtime:
                    max_loadtime = tmp_timing

                template = Template(open(os.path.join(os.path.dirname(__file__),'screenshots.html')).read())
                res = Results(test=command.test, group=RESULT_GROUP.screenshot, status=RESULT_STATUS.info, output_desc = browsername )
                res.output_full = template.render(Context({'filename':screenshot[len(MEDIA_ROOT)+1:],
                                                            'thumb': screenshot_thumb[len(MEDIA_ROOT)+1:],
                                                            'browsername': browsername,
                                                            'browserversion':browser.capabilities['version']}))
                res.save()

                log.debug("Saving screenshot (result:%s)) in: %s "%(res.pk,MEDIA_ROOT+"/"+filename))
                browser.quit()
                signal.alarm(0)

                if browsername == "firefox" and os.path.exists(browser.profile.path):
                    # if alarm was raised, profile could not be deleted
                    shutil.rmtree(browser.profile.path)

            except Alarm:
                log.warning("shoot timeout")


        res = Results(test=command.test, group = RESULT_GROUP.performance, status = RESULT_STATUS.success)
        res.output_desc = unicode(_("Webpage load time"))
        template = Template(open(os.path.join(os.path.dirname(__file__),'pageload.html')).read())
        template_data = {
            'browsernames' : browsernames,
            'timing' : timing,
            'max_loadtime': max_loadtime,
        }


        res.output_full = template.render(Context(template_data))

        if max_loadtime > 5000:
            res.status = RESULT_STATUS.warning
        if max_loadtime > 15000:
            res.status = RESULT_STATUS.error
        res.save()

        display.sendstop()
        #there was no exception - test finished with success
        return STATUS.success
