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
- check spelling [done]

advanced level:
- make list of mispelled words [done]
- find it in html
- change css for it
- do screenshot (subtask: check wheter is posible to do screenshot site in tmp, 
                 or to dynamic in browser add css to elements)
'''


# system imports
import sys
import os
import random
import string
import re
from time import sleep
from datetime import date, datetime, timedelta
from urlparse import urlparse

from django.utils.translation import ugettext_lazy as _


# 3rd party

import mimetypes
import codecs
# pip: nltk
import nltk
# pip: guess_language
import guess_language

# pip: pyenchant
import enchant.checker
from enchant.tokenize import EmailFilter, URLFilter, Filter

# local imports

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from logs import log


try:
    tlds = [
        tld.strip().lower() for tld in open(os.path.join(
                                            os.path.dirname(__file__),
                                            'tlds.txt')).read().splitlines()
    ]
except OSError as e:
    log.exception("Problem with reading tlds.txt from plugin directory",e)

word_regex = re.compile(r'\w+')

def parse_word(url):
    'returns tuple of words (unicodes)'
    url = urlparse(url)
    words = word_regex.findall(url.hostname)
    return words


class BetterURLFilter(Filter):
    _pattern = re.compile(r'.*?(\w+)\.(\w+)$')

    def _skip(self, word):

        #log.debug("Better url word check: %s (%s:%s) =>"%(word, type(word),
        #                                                 len(word)))
        matching = self._pattern.match(word)
        if matching:

            #log.debug(" * match !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            tld = matching.groups()[-1] 
            tld = tld.tounicode()
            stld=tld

            if tld in tlds:
                #log.debug(" * SKIP: last group in tld")
                return True

        #log.info(" * NOT SKIP")
        return False


class PluginCheckSpelling(PluginMixin):
    name = _('Spell checking')
    description = _('Search mistakes in text')
    wait_for_download = True
    max_file_size = 1024*1024 # in bytes

    #: how many occurences of bad word should be in DB to 
    #: classify word as good word
    bad_word_limit = 5 

    #: remove bad words (under the limit from 'bad_word_limit') older than
    #: X days
    bad_word_days = 30


    def spellcheck(self, text, command):
        from scanner.models import (Results, CommandQueue, BadWord)
        # guess language code 
        lang_code, lang_num, lang_name = guess_language.\
                                            guessLanguageInfo(text)
        log.debug('    * check spelling, detected lang: %s (%s)'%(lang_name,
                                                                  lang_code))

        if lang_code == 'UNKNOWN':
            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.info)
            r.output_full = unicode(_('Cannot detect language of page'))
            r.output_desc = unicode(self.name)
            log.warning(' * Cannot detect language of page - end')
            return r,STATUS.unsuccess # .. todo:: is it good status?

        try:
            checker = enchant.checker.SpellChecker(lang_code,
                                       filters=[EmailFilter,
                                                URLFilter,
           #                                     BetterURLFilter,
                                               ])
        except enchant.DictNotFoundError as e:
            log.exception("Cannot find language for spellchecker for %s - end"%\
                          land_code)
            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.info)
            r.output_full = unicode(_('Cannot detect language of page'))
            r.output_desc = unicode(self.name)
            return r,STATUS.warning # .. todo:: what status?

        # checking page for bad words
        log.debug('    * check spelling')
        checker.set_text(text)

        errors = [ er.word for er in checker ] 
        log.debug('      * found %d errors (%s)'%(len(errors),errors))
        log.debug('    * filtering bad words')

        for bad_word in errors:
            BadWord.objects.create(word=bad_word)

        errors = BadWord.filter_bad_words(errors)

        log.debug('      * after filtering out there is %d errors (%s)'%\
                  (len(errors),errors))

        if len(errors):
            # there are some errors
            log.debug('    * there was %s bad word(s)'%len(errors))

            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.error)
            r.output_desc = unicode(self.name)
            resp = u'''<p>You have spelling errors on site:</p>'''
            resp2 =u'<ul>\n'

            for er in errors:
                resp2 += u'<li> %s </li>\n' % er

            resp2 +=u'</ul>\n'

            r.output_full = unicode(_(resp)) + unicode(resp2)
            return r, STATUS.unsuccess

        else:
            # document is clean
            log.debug('    * there was no spelling errors')

            r = Results(test=command.test,
                        group=RESULT_GROUP.general,
                        importance=1,
                        status=RESULT_STATUS.success)
            r.output_full = unicode(_('There is no mispelled words.'))
            r.output_desc = unicode(self.name)
            return r, STATUS.success
        return None, STATUS.exception


    def check_file(self, path, command):
        log.debug(' * file: %s'%path)

        # check if file is type of 'html'
        if 'html' not in str(mimetypes.guess_type(path)[0]):
            log.debug('   * is not html file ')
            return
        else:
            log.debug("   * is html file")

        # read html file and convert it to plain text
        with open(path,'r') as f:
            log.debug("   * opening html file")
            orig = f.read(self.max_file_size) # Max 1 MB of html text file
            try:
                charset = chardet.detect(orig)
            except:
                charset = {'confidence':0.1,
                           'encoding':'ascii'}
            log.debug('    * detected charset: %s'%charset['encoding'])

            try:
                orig = orig.decode(charset['encoding'])
            except:
                pass

            # nltk.clean_html
            # html2text.html2text
            # stripogram.html2text - deprecated buuuu
            # webstemmer - advanced - need site 'learning'
            # boilerpipe - java interface
            # transmogrify.htmlcontentextractor
            # beautifulsoup4
            #
            # The winner is: nltk - fastest and best accurate (imho)
            log.debug('    * cleaning from html to txt')
            text = nltk.clean_html(orig) # .. todo:: handle exception

        result, status = self.spellcheck(text, command)
        log.info(' * stop checking file: %s'%path)
        if not result:
            return 
        else:
            result.save()
            return 

    def run(self, command):
        log.info("Start spellchecking")
        from scanner.models import (Results, CommandQueue)
        import glob
        path = command.test.download_path

        # search html files

        dirs = glob.glob(os.path.join(path,'*%s*'%command.test.domain()))

        log.debug("Search html files in %s "%(dirs))


        for dir in dirs:
            for root, dirs, files in os.walk(dir):
                for file in [ os.path.abspath(os.path.join(root, file))
                                for file in files ]:
                    self.check_file(file, command)

        log.info(' * there was no html files to check spelling')
        return STATUS.success


