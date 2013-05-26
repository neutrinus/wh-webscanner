#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import time
import hashlib

from selenium import webdriver
from selenium.common.exceptions import WebDriverException


browsers = [
	{
		"version": "",
#		"browseName": "internet explorer",
		"browseName": "chrome",

		"platform": "VISTA",
		},
	]
	
url = "http://onet.pl"
SELENIUM_HUB = "http://sv-seleniumhub:4444/wd/hub"
timing = {}
max_loadtime = 0


for browser in browsers:
	browsername = '_'.join([browser[key] for key in 'platform', 'browseName', 'version'])

	print("Make screenshot with %s" % browsername)

	try:
		if browser["browseName"] == "internet explorer":
			desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
		elif browser["browseName"] == "firefox":
			desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
		elif browser["browseName"] == "chrome":
			desired_capabilities = webdriver.DesiredCapabilities.CHROME
		elif browser["browseName"] == "opera":
			desired_capabilities = webdriver.DesiredCapabilities.OPERA
		else:
			print("Browser unknown - please check configuration")
			continue

		if "version" in browser:
			desired_capabilities['version'] = browser["version"]

		if "platform" in browser:
			desired_capabilities['platform'] = browser["platform"]

		dbrowser = webdriver.Remote(
			desired_capabilities=desired_capabilities,
			command_executor=SELENIUM_HUB,
		)

		#http://seleniumhq.org/docs/04_webdriver_advanced.html
		dbrowser.implicitly_wait(30)
		time.sleep(1)
		dbrowser.get(url)

		#give a bit time for loading async-js
		time.sleep(2)

		dbrowser.get_screenshot_as_file("./shoot_%s.png" % browsername)

                timing_data = dbrowser.execute_script("return (window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {}).timing;")
                
                if timing_data and (browser["browseName"] != "internet explorer"):
			timing[browsername] = []
			for _time in ["navigationStart", "domainLookupStart", "domainLookupEnd", "connectStart", "requestStart", "domLoading", "domInteractive", "domComplete", "loadEventEnd"]:
				timing[browsername].append((_time, timing_data[_time] - timing_data["navigationStart"]))
			 
			tmp_timing = timing_data["loadEventEnd"] - timing_data["navigationStart"]
			
			print("Loading took %s milisec" % tmp_timing)
		else:
			print("There was no timing_data for %s" % (browsername))
		

		dbrowser.quit()

		print("Saved screenshot")

	except WebDriverException, e:
		print("WebDriverException: %s" % e)
