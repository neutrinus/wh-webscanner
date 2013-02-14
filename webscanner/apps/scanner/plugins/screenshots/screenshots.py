#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#based on http://maestric.com/doc/python/recursive_w3c_html_validator
import os
import time
import signal
import hashlib
from PIL import Image

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from django.conf import settings

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP
from scanner.plugins.plugin import PluginMixin
from scanner.plugins.optiimg.utils import ImageOptimizer


class Alarm(Exception):
    pass


def alarm_handler(signum, frame):
    raise Alarm


#http://pypi.python.org/pypi/selenium
#https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html
class PluginMakeScreenshots(PluginMixin):
    '''
    This Plugin makes screenshots of a webpage by visiting it using different webbrowsers (firefox,chrome) and selenium.
    '''

    #: this is only used to build two variables below
    SCREENSHOTS_DIR_NAME = getattr(settings, 'WEBSCANNER_SCREENSHOTS_DIR_NAME', 'screenshots')

    name = unicode(_('Screenshots'))
    wait_for_download = False

    browsers = getattr(settings, 'WEBSCANNER_SCREENSHOTS_SELENIUM_BROWSERS', {})

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        if not self.browsers:
            self.log.warning('''You have activated screenshots plugin but you did not set any browsers.
You can do this by specifiying 'WEBSCANNER_SCREENSHOTS_SELENIUM_BROWSERS' dictionary in settings.''')

    def run(self, command):
        url = command.test.url
        from scanner.models import Results

        timing = {}
        max_loadtime = 0

        screenshots_path = os.path.join(command.test.public_data_path, self.SCREENSHOTS_DIR_NAME)
        screenshots_url = os.path.join(command.test.public_data_url, self.SCREENSHOTS_DIR_NAME)
        if not os.path.exists(screenshots_path):
            os.makedirs(screenshots_path)

        for browser in self.browsers:
            screenshot_filename = hashlib.sha1(str(time.time())).hexdigest() + '.png'
            screenshot_file_path = os.path.join(screenshots_path, screenshot_filename)
            screenshot_url = os.path.join(screenshots_url, screenshot_filename)

            browsername = '_'.join([browser[key] for key in 'platform', 'browseName', 'version'])

            self.log.debug("Make screenshot with %s" % browser)

            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(3 * 60)  # 3 minutes

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
                    desired_capabilities['version'] = browser["version"]

                if "platform" in browser:
                    desired_capabilities['platform'] = browser["platform"]

                dbrowser = webdriver.Remote(
                    desired_capabilities=desired_capabilities,
                    command_executor=settings.SELENIUM_HUB,
                )

                #http://seleniumhq.org/docs/04_webdriver_advanced.html
                dbrowser.implicitly_wait(30)
                time.sleep(1)
                dbrowser.get(url)

                #give a bit time for loading async-js
                time.sleep(2)

                dbrowser.get_screenshot_as_file(screenshot_file_path)

                optimizer = ImageOptimizer()
                optimized_screenshot_path = optimizer.optimize_image(screenshot_file_path, screenshots_path)
                if optimized_screenshot_path:
                    # if we have optimized image we do not care about old one
                    os.unlink(screenshot_file_path)
                    screenshot_filename = os.path.basename(optimized_screenshot_path)
                    screenshot_file_path = optimized_screenshot_path
                    screenshot_url = os.path.join(screenshots_url, screenshot_filename)

                timing_data = dbrowser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")

                if timing_data:
                    timing[browsername] = []
                    for _time in ["navigationStart", "domainLookupStart", "domainLookupEnd", "connectStart", "requestStart", "domLoading", "domInteractive", "domComplete", "loadEventEnd"]:
                        timing[browsername].append((_time, timing_data[_time] - timing_data["navigationStart"]))

                    tmp_timing = timing_data["loadEventEnd"] - timing_data["navigationStart"]
                    if tmp_timing > max_loadtime:
                        max_loadtime = tmp_timing
                else:
                    self.log.warning("There was no timing_data for %s" % (browsername))

                dbrowser.quit()
                signal.alarm(0)

                #do it after quiting browser - to save selenium time
                screenshot_thumb_path = self.crop_screenshot(screenshot_file_path)
                screenshot_thumb_url = os.path.join(screenshots_url, os.path.basename(screenshot_thumb_path))

                template = Template(open(os.path.join(os.path.dirname(__file__), 'screenshots.html')).read())
                res = Results(test=command.test, group=RESULT_GROUP.screenshot, status=RESULT_STATUS.info, output_desc=browsername)
                ctx = {'filename': screenshot_url,
                       'thumb': screenshot_thumb_url,
                       'browsername': browsername,
                       'browserversion': dbrowser.capabilities['version']}
                res.output_full = template.render(Context(ctx))
                res.save()
                self.log.debug("Saved screenshot (result:%r))" % res)

            except WebDriverException, e:
                self.log.warning("WebDriverException: %s" % e)
            except Alarm:
                self.log.warning("Shoot timeout")
            finally:
                signal.alarm(0)

        if command.test.check_seo:
            res = Results(test=command.test, group=RESULT_GROUP.performance, status=RESULT_STATUS.success)
            res.output_desc = unicode(_("Webpage load time"))
            template = Template(open(os.path.join(os.path.dirname(__file__), 'pageload.html')).read())
            template_data = {
                'timing': timing,
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

    def crop_screenshot(self, inputfile):
        """ produce a thumb of screenshot in the same dir as original"""
        img = Image.open(inputfile)
        box = (0, 0, 940, 400)
        area = img.crop(box)
        basename, ext = os.path.splitext(inputfile)
        ofile = os.path.join("%s_thumb_%dx%d%s" % (basename, box[2], box[3], '.png'))
        area.save(ofile, 'png')
        return(ofile)
