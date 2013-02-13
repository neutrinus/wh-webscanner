#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__doc__ = '''
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
import re
from urlparse import urlparse

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


# 3rd party

import mimetypes
# pip: nltk
#import nltk
# pip: beautifulsoup4
import bs4

# pip: pyenchant
import enchant.checker
from enchant.tokenize import EmailFilter, URLFilter, Filter

# pip: cchardet
import cchardet

# cld is used now instead of guess_language and guess_language-spirit
# guess_language was a little slow and inaccurate, guess_language-spirit
# was memory inefficient (used enchant dicts but did not free memory)
# pip: chromium_compact_language_detector 0.1.1
import cld

# local imports

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)
from addonsapp.tools import strip_html_tags

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
    raise Exception("Problem with reading tlds.txt from plugin directory",e)
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

    def spellcheck(self, text, tld=''):
        from scanner.models import BadWord
        # guess language code
        self.log.debug('    * guessing language...')
        #lang_code, lang_num, lang_name = guess_language.guessLanguageInfo(text)
        lang_name, lang_code, reliable, bytes_found, details = \
            cld.detect(text.encode('utf-8'), hintTopLevelDomain=tld)
        self.log.debug('    -> detected lang: %s (%s)' % (lang_name, lang_code))

        if lang_code.upper() == 'UNKNOWN' or lang_name.upper() == 'UNKNOWN' or not reliable:
            self.log.warning('    -> Cannot detect language of page - end : %s' % details)
            return None, set()

        self.log.debug('    * searching for dictionary')
        try:
            checker = enchant.checker.SpellChecker(lang_code,
                                                   filters=[EmailFilter,
                                                            URLFilter,
                                                            #  BetterURLFilter,
                                                            ])
        except enchant.DictNotFoundError:
            self.log.error("    -> Cannot find language for spellchecker for %s - end" % lang_code)
            return None, set()

        # checking page for bad words
        self.log.debug('    * check spelling...')
        checker.set_text(text)
        self.log.debug('    -> ok')

        self.log.debug('    * get errors...')
        errors = [er.word for er in checker if len(er.word) < 128]
        self.log.debug('    -> ok')

        self.log.debug('      * found %d bad words and adding them to DB' % len(errors))
        BadWord.objects.bulk_create(
            [BadWord(word=bad_word.strip().lower()) for bad_word in errors])
        self.log.debug('      -> ok')

        self.log.debug('     * call filtering bad words')
        errors = BadWord.filter_bad_words(errors)
        self.log.debug('      -> ok')

        self.log.debug('     * after filtering out there is %d errors (%s)' % (len(errors), errors))

        return lang_name, set(errors)

    def check_file(self, path):
        self.log.debug(' * check spelling in file: %s' % path)

        # check if file is type of 'html'
        if 'html' not in str(mimetypes.guess_type(path)[0]):
            self.log.debug('   * is not html file, omitting')
            return None, set()
        else:
            self.log.debug("   * is html file")

        # read html file and convert it to plain text
        with open(path, 'r') as f:
            self.log.debug("   * reading html file...")
            orig = f.read(self.max_file_size)  # Max 1 MB of html text file

            self.log.debug("   -> file loaded")
            self.log.debug('   * detecting charset...')
            try:
                charset = cchardet.detect(orig)
            except Exception:
                charset = {'confidence': 0.1, 'encoding': 'ascii'}
                self.log.warning('    -> error while detecting charset')
            self.log.debug('    -> detected charset: %s' % charset['encoding'])
            if not charset['encoding']:
                self.log.debug('    -> set default encoding (ascii)')
                charset['encoding'] = 'ascii'

            self.log.debug('    * decoding text...')
            try:
                orig = orig.decode(charset['encoding'])
            except Exception:
                self.log.warning('    -> error while decoding text')
                self.log.info('     * try cleaning without decoding')
                #raise CannotDecode(e)
            self.log.debug('    -> ok')

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
            self.log.debug('    * cleaning from html to txt...')
            try:
                #text = nltk.clean_html(orig)
                text = '\n'.join(strip_html_tags(bs4.BeautifulSoup(orig).html.body))
            except Exception:
                self.log.warning('    * error while cleaning html, omitting file')
                return None, set()
            self.log.debug('    -> ok')

        lang, errors = self.spellcheck(text)
        self.log.info(' * stop checking file: %s' % path)
        return lang, errors

    def run(self, command):
        self.log.info(" * check spelling: BEGIN")
        from scanner.models import Results
        import glob
        path = str(command.test.download_path)

        # search html files

        dirs = glob.glob(os.path.join(path, '*%s*' % command.test.domain()))

        self.log.debug("Search html files in %s " % (dirs,))

        files_with_errors = []
        was_errors = False
        for dir in dirs:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))
                    try:
                        lang, errors = self.check_file(file_path)
                    except CheckSpellingError as e:
                        self.log.exception(" * Spellchecking error: %s", e)
                        errors = set()
                        was_errors = True
                        continue
                    if errors:
                        errors = list(errors)

                        files_with_errors.append([os.path.relpath(file_path, path),
                                                  lang,
                                                  errors])

        template = Template(open(os.path.join(os.path.dirname(__file__),
                                              'templates/msg.html')).read())
        r = Results(test=command.test,
                    group=RESULT_GROUP.general,
                    importance=1,
                    status=RESULT_STATUS.warning if files_with_errors else
                    RESULT_STATUS.success)
        r.output_desc = unicode(self.name)
        r.output_full = template.render(Context({'files': files_with_errors}))
        r.save()

        self.log.info(' * check spelling: END')

        if was_errors:
            return STATUS.unsuccess
        return STATUS.success
