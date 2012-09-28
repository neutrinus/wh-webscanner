#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
#http://code.google.com/p/pywhois/
import random
import HTMLParser
import urllib
import urlparse
import random
import string
import re
import shlex, subprocess
from time import sleep
from datetime import date
from plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from logs import log


#PATH_KASPERSKY = '/'
PATH_CLAMSCAN = '/usr/bin/clamscan'
PATH_WGET = '/usr/bin/puf'
PATH_TMPSCAN = '/tmp/clamdd/'


class PluginClamav(PluginMixin):
    name = unicode(_('Clamscan'))

    def run(self, command):
        if not command.test.check_security:
            return STATUS.success
        try:
            #scan website
            cmd = PATH_CLAMSCAN + " "+ command.test.download_path
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE)
            (output, stderrdata2) = p.communicate()
            if p.returncode != 0:
                log.exception("%s returned non-0 status, stderr: %s "%(PATH_CLAMSCAN,stderrdata2))
                return STATUS.exception

            numberofthreats = int(re.search('Infected files: (?P<kaczka>[0-9]*)',output).group('kaczka'))

            from scanner.models import Results
            res = Results(test=command.test,group = RESULT_GROUP.security, importance=5)
            res.output_desc = unicode(_("Antivirus check"))

            if numberofthreats > 0:
                res.status = RESULT_STATUS.error
                res.output_full = unicode(_("Our antivirus found <b>%s</b> infected files on your website"%(numberofthreats)))
            else:
                res.status = RESULT_STATUS.success
                res.output_full = unicode(_("Our antivirus claims that there is no infected files on your website."))
            res.save()

            #as plugin finished - its success
            return STATUS.success
        except OSError,e:
            log.error("OSError, check if clamscan file is present. Details %s "%(e))
            return STATUS.exception




if __name__ == '__main__':
    main()
