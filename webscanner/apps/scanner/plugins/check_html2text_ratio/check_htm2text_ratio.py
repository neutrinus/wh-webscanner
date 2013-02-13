#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import sys
import bs4
import mimetypes
import glob

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
import dns.resolver
import dns.reversename
from IPy import IP
import smtplib

from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from addonsapp.tools import strip_html_tags

class PluginHtml2TextRatio(PluginMixin):
    name = unicode(_('Code to text ratio'))
    wait_for_download = True

    def run(self, command):

        if not command.test.check_seo:
            return

        from scanner.models import Results

        chars_total = 0.0
        chars_text = 0.0
        path = str(command.test.download_path)

        for dir in glob.glob(os.path.join(path,'*%s*'%command.test.domain())):
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))
                    if 'html' not in str(mimetypes.guess_type(file_path)[0]):
                        continue
                    self.log.debug('analizing file %s' % file_path)
                    with open(file_path, 'r') as f:
                        orig = f.read()

                        chars_total += len(str(orig))
                        chars_text +=  len('\n'.join(strip_html_tags(bs4.BeautifulSoup(orig))))
                        #print "file: %s; (%s / %s)" % (file_path, chars_text, chars_total)

        if chars_total:
            ratio = chars_text / chars_total
        else:
            ratio = 0.0

        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=2)
        res.output_desc = unicode(_("Code to content ratio "))
        if ratio > 0.25 and ratio < 0.70:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>Good, your code to text ratio is  %s</p>"%(ratio ) ))
        else:
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("<p>BAAAD, your code to text ratio is  %s</p>"%(ratio)))

        #res.output_full += unicode(_("<p>total: %s, text:%s</p>"%(chars_total, chars_text ) ))

        res.save()

        return STATUS.success


