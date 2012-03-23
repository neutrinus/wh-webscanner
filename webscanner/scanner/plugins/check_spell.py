#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__doc__='''
Enchant backend: hunspell

requirements.pip: pyenchant guess-language html2text
requirements.debian: enchant hunspell-*?

algorithm
---------

- extract text from html [done]
- guess language [done]
- check spelling

advanced level:
- make list of mispelled words
- find it in html
- change css for it
- do screenshot
'''


# system imports
import sys
import os
import random
import string
import re
from time import sleep
from datetime import date

from django.utils.translation import ugettext_lazy as _

# 3rd party

import mimetypes
import codecs
import html2text
import guess_language
import enchant.checker
from enchant.tokenize import EmailFilter, URLFilter

# local imports

from plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)


from logs import log


class PluginSpellCheck(PluginMixin):
    name = unicode(_('Spell checking'))
    description = _('Search mistakes in text')
    wait_for_download = True
    max_file_size = 1024*1024 # in bytes

    def spellcheck(self, text, command):
        from scanner.models import (Results, CommandQueue)
        # guess language code 
        lang_code, lang_num, lang_name = guess_language.\
                                            guessLanguageInfo(text)

        if lang_code == 'UNKNOWN':
            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.info)
            r.output_full = unicode(_('Cannot detect language of page'))
            r.output_desc = self.name
            log.warning('Cannot detect language of page')
            return r,STATUS.unsuccess # .. todo:: is it good status?

        try:
            checker = enchant.checker.SpellChecker(lang_code,
                                       filters=[EmailFilter,URLFilter])
        except enchant.DictNotFoundError as e:
            log.exception("Cannot find language for spell checker for %s"%\
                          land_code)
            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.info)
            r.output_full = unicode(_('Cannot detect language of page'))
            r.output_desc = self.name
            return r,STATUS.warning # .. todo:: what status?

        # checking page
        checker.set_text(text)

        errors = [ er.word for er in checker ] 

        if len(errors):
            # there are some errors

            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.error)
            r.output_desc = self.name
            resp = '''<p>You have spelling errors on site:</p>'''
            resp2 =u'<ul>\n'

            for er in errors:
                resp2 += '<li> %s </li>\n' % er

            resp2 +=u'</ul>\n'

            r.output_full = unicode(_(resp)) + unicode(resp2)
            return r, STATUS.unsuccess

        else:
            # document is clean

            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.success)
            r.output_full = unicode(_('There is no mispelled words.'))
            r.output_desc = self.name
            return r, STATUS.success
        return None, STATUS.exception

    def run(self, command):
        log.info("Start spellchecking")
        from scanner.models import (Results, CommandQueue)

        # search html files
        log.debug("Search html files in %s "%(command.test.download_path))
        for root, dirs, files in os.walk(command.test.download_path):
            for file in [ os.path.abspath(os.path.join(root, file))
                            for file in files ]:

                # check if file is type of 'html'
                if 'html' not in str(mimetypes.guess_type(file)[0]):
                    continue

                # read html file and convert it to plain text
                with open(file,'r') as f:
                    orig = f.read(self.max_file_size) # Max 1 MB of html text file
                    try:
                        charset = chardet.detect(orig)
                    except:
                        charset = {'confidence':0.1,
                                   'encoding':'ascii'}

                    try:
                        orig = orig.decode(charset['encoding'])
                    except:
                        pass

                    text = html2text.html2text(orig) # .. todo:: handle exception

                result, status = self.spellcheck(text, command)
                if not result:
                    return STATUS.exception
                else:
                    result.save()
                    return status


