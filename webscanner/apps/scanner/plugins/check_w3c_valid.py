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
from time import sleep
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

w3c_validator = 'http://validator.w3.org/'


class PluginCheckW3CValid(PluginMixin):

    name = unicode(_('W3C Validator'))
    description = unicode(_('Check whether site is in w3c code'))
    wait_for_download = False

    def run(self, command):
        domain = command.test.url

        # urllib requires bytestring
        checklink = '{}check?uri={}'.format(w3c_validator, domain.encode('utf-8'))
        result = urllib.urlopen(checklink)

        output = "status: %s, warnings: %s, errors: %s."%(
                str(result.info().getheader('x-w3c-validator-status')),
                str(result.info().getheader('x-w3c-validator-warnings')),
                str(result.info().getheader('x-w3c-validator-errors')))

        from scanner.models import Results
        res = Results(test=command.test, group = RESULT_GROUP.general, importance=2)
        res.output_desc = unicode(_("W3C Validation"))

        if result.info().getheader('x-w3c-validator-status') == 'Valid' :
            res.status = RESULT_STATUS.success
            res.output_full = '<p>W3C Validator marks your website as <b>Valid</b>. %s <a href="%s">Check details at W3C</a></p>'%(output,checklink)
        else:
            res.status = RESULT_STATUS.warning
            res.output_full = '<p>W3C Validator marks your website as <b>Invalid</b>. %s <a href="%s">Check details at W3C</a></p>'%(output,checklink)

        #TODO
        res.output_full += unicode(_("<p>Complying with web standards enhances interoperability and may result in better google position </p> "))

        res.save()

        #there was no exception - test finished with success
        return STATUS.success

