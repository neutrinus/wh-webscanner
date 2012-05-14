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
from django.template import Template, Context


# 3rd party

import mimetypes
import codecs
# pip: nltk
#import nltk
# pip: beautifulsoup4
import bs4
# pip: guess_language
import guess_language

# pip: pyenchant
import enchant.checker
from enchant.tokenize import EmailFilter, URLFilter, Filter

# pip: chardet
import chardet

# local imports

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from logs import log

class CheckSpellingError(Exception):pass
class NoDictionary(CheckSpellingError):pass
class CannotGuessEncoding(CheckSpellingError):pass
class CannotGuessLanguage(CheckSpellingError):pass
class LanguageNotInstalled(CheckSpellingError):pass
class CannotDecode(CheckSpellingError):pass
class CannotCleanHTML(CheckSpellingError):pass

try:
    tlds = [
        tld.strip().lower() for tld in open(os.path.join(
                                            os.path.dirname(__file__),
                                            'tlds.txt')).read().splitlines()
    ]
except OSError as e:
    log.exception("Problem with reading tlds.txt from plugin directory",e)
    sys.exit(1)


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


    def spellcheck(self, text):
        from scanner.models import (Results, CommandQueue, BadWord)
        # guess language code 
        lang_code, lang_num, lang_name = guess_language.\
                                            guessLanguageInfo(text)
        log.debug('    * check spelling, detected lang: %s (%s)'%(lang_name,
                                                                  lang_code))

        if lang_code == 'UNKNOWN':
            log.warning('    * Cannot detect language of page - end')
            # 
            # raise CannotGuessLanguage()
            return None,set()

        try:
            checker = enchant.checker.SpellChecker(lang_code,
                                       filters=[EmailFilter,
                                                URLFilter,
        #                                       BetterURLFilter,
                                               ])
        except enchant.DictNotFoundError as e:
            log.error("Cannot find language for spellchecker for %s - end"%\
                          lang_code)
            #raise e
            return None,set()

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

        return lang_name, set(errors)


    def check_file(self, path):
        log.debug(' * file: %s'%path)

        # check if file is type of 'html'
        if 'html' not in str(mimetypes.guess_type(path)[0]):
            log.debug('   * is not html file ')
            return None, set()
        else:
            log.debug("   * is html file")

        # read html file and convert it to plain text
        with open(path,'r') as f:
            log.debug("   * opening html file")
            orig = f.read(self.max_file_size) # Max 1 MB of html text file
            log.debug("   * file loaded")
            try:
                charset = chardet.detect(orig)
            except Exception as e:
                charset = {'confidence':0.1,
                           'encoding':'ascii'}
                log.warning('    * error while detecting charset')
            log.debug('    * detected charset: %s'%charset['encoding'])
            if not charset['encoding']:
                log.debug('    * set default encoding (ascii)')
                charset['encoding'] = 'ascii'


            try:
                orig = orig.decode(charset['encoding'])
            except Exception as e:
                log.warning('    * error while decoding text')
                log.info('     * try cleaning without decoding')
                #raise CannotDecode(e)

            def strip_script_tags(root):
               for s in root.childGenerator():
                 if hasattr(s, 'name'):    # then it's a tag
                   if s.name == 'script':  # skip it!
                     continue
                   for x in strip_script_tags(s): yield x
                 else:                     # it's a string!
                   yield s

            # nltk.clean_html
            # html2text.html2text
            # stripogram.html2text - deprecated buuuu
            # webstemmer - advanced - need site 'learning'
            # boilerpipe - java interface
            # transmogrify.htmlcontentextractor
            # beautifulsoup4
            #
            # The winner is: nltk - fastest and best accurate (imho)
            # - noooooooo, nltk works not well with different encodings
            log.debug('    * cleaning from html to txt')
            try:
                #text = nltk.clean_html(orig) 
                text = '\n'.join(strip_script_tags(
                            bs4.BeautifulSoup(orig).html.body
                ))
            except Exception as e:
                log.warning('    * error while cleaning html, omitting file')
                return None, set()

        lang, errors = self.spellcheck(text)
        log.info(' * stop checking file: %s'%path)
        return lang, errors

    def run(self, command):
        log.info("Start spellchecking")
        from scanner.models import (Results, CommandQueue)
        import glob
        path = str(command.test.download_path)

        # search html files

        dirs = glob.glob(os.path.join(path,'*%s*'%command.test.domain()))

        log.debug("Search html files in %s "%(dirs))

        files_with_errors = []
        was_errors = False
        for dir in dirs:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))
                    try:
                        lang, errors = self.check_file(file_path)
                    except CheckSpellingError as e:
                        log.exception(" * Spellchecking error: %s",e)
                        errors=set()
                        was_errors=True
                        continue
                    if errors:
                        files_with_errors.append( [os.path.join(
                                os.path.relpath(file_path,path),
                            ),
                            lang,
                            errors,
                        ])


        template = Template(open(os.path.join(os.path.dirname(__file__),
                                              'templates/msg.html')).read())
        r = Results(test=command.test,
                    group=RESULT_GROUP.general,
                    importance=1,
                    status=RESULT_STATUS.warning if files_with_errors else\
                           RESULT_STATUS.success)
        r.output_desc = unicode(self.name)
        r.output_full = template.render(Context({'files':files_with_errors}))
        r.save()

        log.info(' * check spelling: END')

        if was_errors:
            return STATUS.unsuccess
        return STATUS.success




