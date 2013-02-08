import logging

import mock
import pytest
from unittest import TestCase

from scanner.models import *
from .check_http_code import PluginCheckHTTPCode as Plug

@pytest.mark.django_db
class TestCode(TestCase):
    def setUp(self):
        self.plugin = Plug()

    def test_non_existance_domain(self):
        test = Tests(url='http://dsafdsafa324324239421432rji41111111111.tld',
                    )
        test.save()
        cmd = CommandQueue(
                        test=test,
                        testname='???')
        cmd.save()

        self.log.info('check site %s'%test)
        assert self.plugin.run(cmd) == STATUS.exception


    def test_non_existance_domain(self):
        Results.objects.all().delete()
        test = Tests(url='http://asd213120asod.pl',
                    )
        test.save()
        cmd = CommandQueue(
                        test=test,
                        testname='???')
        cmd.save()

        # fake response object
        resp = mock.Mock()
        resp.status = 200
        resp.getheaders.return_value = [('a','b')]
        resp.getheader.return_value = None

        # fake getattrinfo method (is used by HTTPConncection)
        mock1 = mock.patch('socket.getaddrinfo',
                           return_value=[(2, 1, 6, '', ('213.180.146.27', 80))])

        # fake HTTPConnection to return faked response
        mock2 = mock.patch('httplib.HTTPConnection.getresponse',
                           return_value=resp)

        mock1.start(), mock2.start()

        assert self.plugin.run(cmd) == STATUS.success

        mock1.stop(), mock2.stop()

        assert Results.objects.all()[0].status == RESULT_STATUS.success
        assert Results.objects.all()[1].status == RESULT_STATUS.warning

        Results.objects.all().delete()

        # now, check with http encoding
        resp.getheader.return_value = 'gzip'

        mock1.start(), mock2.start()
        assert self.plugin.run(cmd) == STATUS.success
        mock1.stop(), mock2.stop()

        assert Results.objects.all()[0].status == RESULT_STATUS.success
        assert Results.objects.all()[1].status == RESULT_STATUS.success
