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
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from PIL import Image

from scanner.plugins.optiimg import gentmpfilename, optimize_image
from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP



class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

def crop_screenshot(inputfile):
    """ produce a thumb of screenshot """
    img = Image.open(inputfile)
    box = (0, 0, 940, 400)
    area = img.crop(box)
    ofile = os.path.join(settings.MEDIA_ROOT,"/screenshots/", "thumb_"+gentmpfilename()+".png")
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

    browsers = [
        #{
            #"version": "",
            #"browseName": "opera",
            #"platform": "LINUX",
        #},
        {
            "version": "",
            "browseName": "opera",
            "platform": "WINDOWS",
        },
        {
            "version": "",
            "browseName": "chrome",
            "platform": "LINUX",
        },
        {
            "version": "",
            "browseName": "chrome",
            "platform": "WINDOWS",
        },
        {
            "version": "4.0",
            "browseName": "firefox",
            "platform": "WINDOWS",
        },
        {
            "version": "4.0",
            "browseName": "firefox",
            "platform": "LINUX",
        },
        {
            "version": "7.0",
            "browseName": "firefox",
            "platform": "LINUX",
        },
        {
            "version": "7.0",
            "browseName": "firefox",
            "platform": "WINDOWS",
        },
        {
            "version": "10.0",
            "browseName": "firefox",
            "platform": "LINUX",
        },
        {
            "version": "10.0",
            "browseName": "firefox",
            "platform": "WINDOWS",
        },
        {
            "version": "8",
            "browseName": "iexplore",
        },
    ]

    def run(self, command):
        url = command.test.url
        from scanner.models import Results

        timing = {}
        max_loadtime = 0

        for browser in self.browsers:
            filename = os.path.join ('screenshots/', ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) + ".png")

            browsename =""
            for key in browser:
                browsename += "_" + str(browser[key])

            self.log.debug("Make screenshot with %s" % browser)

            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(3*60)  # 3 minutes

            try:
                if browser["browseName"] == "iexplore":
                    desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
                elif browser["browseName"] == "firefox":
                    desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
                elif browser["browseName"] == "chrome":
                    desired_capabilities = webdriver.DesiredCapabilities.CHROME
                elif browser["browseName"] == "opera":
                    desired_capabilities = webdriver.DesiredCapabilities.OPERA
                else:
                    self.log.warning("Browser unknown - please check configuration")
                    continue

                if "version" in browser:
                    desired_capabilities['version'] =  browser["version"]

                if "platform" in browser:
                    desired_capabilities['platform'] =  browser["platform"]

                dbrowser = webdriver.Remote(
                    desired_capabilities=desired_capabilities,
                    command_executor=settings.SELENIUM_HUB,
                )

                #http://seleniumhq.org/docs/04_webdriver_advanced.html
                dbrowser.implicitly_wait(30)
                sleep(1)
                dbrowser.get(url)

                #give a bit time for loading async-js
                sleep(2)

                dbrowser.get_screenshot_as_file(os.path.join(settings.MEDIA_ROOT,filename))

                timing_data = dbrowser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")

                timing[browsername] = []

                for time in ["navigationStart","domainLookupStart","domainLookupEnd","connectStart","requestStart", "domLoading","domInteractive","domComplete","loadEventEnd"]:
                    timing[browsername].append( (time, timing_data[time] - timing_data["navigationStart"]))

                tmp_timing =  timing_data["loadEventEnd"] - timing_data["navigationStart"]
                if tmp_timing > max_loadtime:
                    max_loadtime = tmp_timing

                dbrowser.quit()
                signal.alarm(0)

                thumb = crop_screenshot(os.path.join(settings.MEDIA_ROOT, filename))

                template = Template(open(os.path.join(os.path.dirname(__file__),'screenshots.html')).read())
                res = Results(test=command.test, group=RESULT_GROUP.screenshot, status=RESULT_STATUS.info, output_desc = browsername )
                res.output_full = template.render(Context({'filename':screenshot[len(settings.MEDIA_ROOT)+1:],
                                                            'thumb': screenshot_thumb[len(settings.MEDIA_ROOT)+1:],
                                                            'browsername': browsername,
                                                            'browserversion': dbrowser.capabilities['version']}))
                res.save()
                self.log.debug("Saved screenshot (result:%s)) in: %s "%(res.pk, os.path.join(settings.MEDIA_ROOT,filename)))

            except WebDriverException,e:
                self.log.exception("WebDriverException")

            except Alarm:
                self.log.warning("Shoot timeout")
                pass

        if command.test.check_seo:
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

        #there was no exception - test finished with success
        return STATUS.success
