# -*- encoding: utf-8 -*-
import mock
from unittest import TestCase
import logging

from ..models import *
from check_spell import PluginSpellCheck as Plug


class TestCode(TestCase):
    def setUp(self):
        self.plugin = Plug()
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

