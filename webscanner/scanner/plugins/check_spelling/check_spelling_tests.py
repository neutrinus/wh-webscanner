# -*- encoding: utf-8 -*-
import os
import mock
from unittest import TestCase
import logging
import enchant
import chardet
import nltk

from ...models import *
from check_spelling import PluginCheckSpelling as Plug, BetterURLFilter, tlds

def abspath(p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),p))


class TestCode(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.delete('bad_words')
        self.plugin = Plug()
        self.plugin.bad_words_limit = 5
        Tests.objects.all().delete()
        CommandQueue.objects.all().delete()

        self.test =test = Tests(url='http://dsafdsafa324324239421432rji41111111111.tld',
                     priority=0,
                    )
        test.save()
        self.cmd= cmd = CommandQueue(
                        test=test,
                        testname='???')
        cmd.save()
        self.path = os.path.join(
                        os.path.dirname(__file__),
                        'tests_htmls')

    def test_undetected_language(self):
        pl = self.plugin
        assert pl.spellcheck("sadagaewqr",self.cmd)[1] == STATUS.unsuccess 

    def test_pl_ok(self):
        pl = self.plugin
        t1_ok='''Litwo ojczyzno moja ty jesteś jak zdrowie ile Cię trzeba cenić ten tylko
        się dowie
        '''
        assert pl.spellcheck(t1_ok,self.cmd)[1] == STATUS.success

    def test_pl_1error(self):
        pl = self.plugin
        # check pl lang - 1 error
        t1_fail='''Litwo ojczyznw moja ty jesteś jak zdrowie ile Cię trzeba cenić ten tylko
        się dowie
        '''
        assert 'ojczyznw' in pl.spellcheck(t1_fail,self.cmd)[0].output_full

    def test_filtering_bad_words(self):
        pl = self.plugin

        # add some words
        for w in ['witaj','kotku','w','moim','młotku']:
            BadWord.objects.create(word=w)

        # all words shoul pass, because limit was not reached
        assert BadWord.filter_bad_words(['amazon','google','kotku'])\
                == ['amazon', 'google', 'kotku']

        for w in ['kotku']*10:
            BadWord.objects.create(word=w)

        assert BadWord.filter_bad_words(['amazon','google','kotku'])\
                == ['amazon', 'google']

    def test_cleaning_bad_words(self):
        pl = self.plugin
        olds = ['stare','stare2']
        for w in olds:
            BadWord.objects.create(word=w)

        BadWord.objects.all().update(timestamp = dt.now() - td(days=100))
        for w in ['nowe','nowe2']:
            BadWord.objects.create(word=w)

        assert BadWord.objects.all().count() == 4

        BadWord.clean_bad_words()

        assert BadWord.objects.all().count() == 2
        

    def test_checker_regexp(self):
        b=BetterURLFilter
        words = ['gazeta.pl','amazon.co.uk','amazon.com',
                 'google.com',
                 'apteka.pana.kleksa.net',
                ]
        import array
        words = [ array.array('c',x) for x in words ]

        # TODO: better handling this shit
        #                 'glupi.pl/url'

        words2 = ['paskowi.', 'w domu.','pan tik tak','grzegorz']

        log.debug('TLDS: %s'%tlds)
        log.debug('BetterURLFilter REGEXP TEST: %s'%b._pattern.pattern)

        log.debug('Should match!')
        for word in words:
            word=word.tostring()
            word=word.strip().lower()
            log.debug('Test word: %s (%s:%s)'%(word, type(word), len(word)))
            match = b._pattern.match(word)
            log.debug(" * %s"%bool(match))
            assert match
            tld = match.groups()[-1].strip().lower()
            log.debug(' * checking "%s" is in tld: %s'%(tld, tld in tlds))
            assert  tld in tlds

        log.debug('Should not match!!!')
        for word in words2:
            word=word.strip().lower()
            log.debug('Test word: %s'%word)
            match = b._pattern.match(word)
            log.debug(" * %s"%(bool(match)))
            assert not match


        

    def test_checker_with_better_url_filter(self):
        #pl = self.plugin
        log.debug('Better URL FILTER class TEST')

        words = set(['gazeta.pl','amazon.co.uk','amazon.com',
                 'google.com',
                 'apteka.pana.kleksa.net',
                 u'ołkej.pl',
               #  'glupi.pl/url'

        ])
        bad_words = set([
                 u'badfdsagfafaf',u'fadfasfd',u'dafafadf',u'Witaj',
                u'strona.notintld',
        ])

        bad_words_to_check = set([
        x.lower().strip()
        for word in bad_words
            for x in word.split('.')
        ])


        words = words.union( bad_words )

        checker = enchant.checker.SpellChecker('en', filters=[
                        BetterURLFilter,            
        ]) 

        sentence = u' '.join(words)

        log.debug('checker: %s'%checker)

        log.debug('checker text: %s'%sentence)
        checker.set_text(sentence)

        errors = set([w.word for w in checker])

        log.debug("checker errors: %s"%(errors))
        log.debug('bad_words:      %s'%bad_words_to_check)


        assert len(errors) == len(bad_words_to_check)


    def test_onet(self):
        log.debug("CHECKING ONET !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        pl = self.plugin
        f = open(abspath('tests_htmls/onet.html')).read() 
        charset = chardet.detect(f)['encoding']
        f=f.decode(charset)
        f=nltk.clean_html(f)

        checker = enchant.checker.SpellChecker('pl', filters=[
                        BetterURLFilter,            
        ]) 
        checker.set_text(f)
        errors = [ e.word for e in checker ]



        bad_words = ['VOD','Onet','mWIG','multi']
        for w in bad_words:
            for z in xrange(20):
                BadWord.objects.create(word=w.lower())
        cache.delete('bad_words')

        errors = BadWord.filter_bad_words(errors)
        log.error('ERRORS: %s'%errors)
        assert 1==2


    def check_wykop(self):
        pl = self.plugin
        pass

    def check_amazon(self):
        pl = self.plugin
        pass
