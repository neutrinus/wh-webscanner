#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import string
import re
from time import sleep
from datetime import date
from plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _


class PluginPlainTextEmail(PluginMixin):
    '''
    Look for plain text emails in html files
    '''
    name = unicode(_('PlainTextEmails'))
    wait_for_download = True

    def run(self, command):
        path = command.test.download_path + "/"
        efound = ""

        try:
            self.log.debug("Recursive search for plaintext emails in %s "%(path))

            # We want to recurslivly grep all html files and look for something looking like email address
            filelist = []
            for root, dirs, files in os.walk(str(path)):
                for file in files:
                    if re.search('(.html)|(.php)|(.xml)|(.txt)|(.htm)|(.js)',file) is not None:
                        filelist.append(os.path.join(root,file))


            for file in filelist:
                #log.debug("Analizing file %s "%(file))
                memFile = open(file)
                for line in memFile.readlines():
                    match = re.search("[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}",line)
                    if match is not None:
                        efound += "%s found in %s <br />"%(match.group(), file[len(path):])
                memFile.close()

            from scanner.models import Results
            res = Results(test=command.test,group = RESULT_GROUP.mail, importance=5)
            res.output_desc = unicode(_("Look for plain-text email addreses"))
            res.output_full = unicode(_("<p>Spammers use automatic <a href='http://en.wikipedia.org/wiki/Email_address_harvesting'>email harvesters</a> to send SPAM to email addresses found on websites. To avoid being spammed you shoud not put your email as plaintext on your webpage. Use some of cloaking techniques instead.</p>"))

            #TODO: list possible techniques

            if efound:
                res.status = RESULT_STATUS.warning
                res.output_full += unicode(_("<p>We have found at least one email address on your website! Please review your website and remove email addreses or obfuscate them. </p>"))
            else:
                res.status = RESULT_STATUS.success
                res.output_full += unicode(_("<p>OK, we did not found any plaintext e-mail addreses on your website.</p>"))
            res.save()

            #as plugin finished - its success
            return STATUS.success
        except Exception,e:
            self.log.exception("No check can be done: %s "%(e))
            return STATUS.exception




if __name__ == '__main__':
    main()
