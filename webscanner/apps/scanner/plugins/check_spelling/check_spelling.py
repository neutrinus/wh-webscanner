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
import os

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


# 3rd party

import mimetypes

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
from webscanner.utils.html import clean_html
from webscanner.utils.http import check_effective_tld


class CheckSpellingError(Exception):
    pass


class NoDictionary(CheckSpellingError):
    pass


class CannotGuessEncoding(CheckSpellingError):
    pass


class CannotGuessLanguage(CheckSpellingError):
    pass


class LanguageNotInstalled(CheckSpellingError):
    pass


class CannotDecode(CheckSpellingError):
    pass


class CannotCleanHTML(CheckSpellingError):
    pass


class BetterURLFilter(Filter):

    def _skip(self, word):
        try:
            check_effective_tld(word)
            return True
        except ValueError:
            return False


class PluginCheckSpelling(PluginMixin):
    name = _('Spell checking')
    description = _('Search mistakes in text')
    wait_for_download = True
    max_file_size = 1024 * 1024  # in bytes

    not_supported_lang = ['xxx', 'tr', 'id', 'mt', 'ka', 'az']

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
            if lang_code in self.not_supported_lang:
                self.log.debug("    -> Cannot find language for spellchecker for %s - end (blacklisted)" % lang_code)
            else:
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

            # nltk.clean_html - slow
            # html2text.html2text - not accurate
            # stripogram.html2text - deprecated buuuu
            # webstemmer - advanced - need site 'learning'
            # boilerpipe - java interface
            # transmogrify.htmlcontentextractor
            # beautifulsoup4
            #
            # The winner is: nltk - fastest and best accurate (imho)
            # - noooooooo, nltk does not work well with different encodings
            self.log.debug('    * cleaning from html to txt...')
            try:
                #text = nltk.clean_html(orig) - a little slow, problem with encodings
                text = clean_html(orig)
            except Exception as error:
                self.log.warning('    * error while cleaning html, omitting file: %s' % error)
                return None, set()
            self.log.debug('    -> ok')

        lang, errors = self.spellcheck(text)
        self.log.info(' * stop checking file: %s' % path)
        return lang, errors

    def run(self, command):
        self.log.info(" * check spelling: BEGIN")
        from scanner.models import Results
        path = str(command.test.download_path)

        # search html files

        files_with_errors = []
        was_errors = False
        for file_info in command.test.downloaded_files:
            if not 'text' in file_info['mime']:
                continue
            file_path = os.path.join(path, file_info['path'])
            try:
                lang, errors = self.check_file(file_path)
            except CheckSpellingError as e:
                self.log.exception(" * Spellchecking error: %s", e)
                errors = set()
                was_errors = True
                continue
            if errors:
                errors = list(errors)

                files_with_errors.append({'url': file_info['url'],
                                          'detected_language': lang,
                                          'spelling_errors': errors})

        template = Template(open(os.path.join(os.path.dirname(__file__),
                                              'templates/msg.html')).read())
        r = Results(test=command.test,
                    group=RESULT_GROUP.general,
                    importance=1,
                    status=RESULT_STATUS.warning if files_with_errors else
                    RESULT_STATUS.success)
        r.output_desc = unicode(self.name)
        r.output_full = template.render(Context({'urls': files_with_errors}))
        r.save()

        self.log.info(' * check spelling: END')

        if was_errors:
            return STATUS.unsuccess
        return STATUS.success
