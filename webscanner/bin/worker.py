#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../')
sys.path.append('./')

import settings
setup_environ(settings)

import os
import random
import logging
import subprocess
import shlex
import urlparse
from time import sleep
from datetime import datetime
#from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db.models import Q
from multiprocessing import Pool, cpu_count
from scanner.models import Tests, CommandQueue, STATUS, PLUGINS

#log = logging.getLogger('webscanner.worker')

#from logs import log

PATH_HTTRACK = '/usr/bin/httrack'


def worker():
    log = logging.getLogger('webscanner.worker.scanner')
    log.debug("Starting new worker pid=%s" % (os.getpid()))
    sleep(random.uniform(0, 5))

    #main program loop
    while(True):
        try:
            #log.debug('Try to fetch some fresh stuff')
            with transaction.commit_on_success():
                try:
                    ctest = CommandQueue.objects.filter(status=STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status=STATUS.success)).order_by('?')[:1].get()

                    #this should dissallow two concurrent workers for the same commandqueue object
                    commandschanged = CommandQueue.objects.filter(status=STATUS.waiting).filter(pk=ctest.pk).update(status=STATUS.running)

                    if (commandschanged == 0):
                        log.debug("Someone already took care of this ctest(%r)" % ctest)
                        ctest = None
                        sleep(random.uniform(2, 10))  # there was nothing to do - we can sleep longer
                        continue

                    ctest.status = STATUS.running
                    ctest.run_date = datetime.utcnow()
                    ctest.save()
                    log.info('Processing command %s(%s) for %s (queue len:%s)' % (ctest.testname, ctest.pk, ctest.test.url, CommandQueue.objects.filter(status=STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status=STATUS.success)).count()))
                except CommandQueue.DoesNotExist:
                    ctest = None
                    log.debug("No Commands in Queue to process, sleeping.")
                    sleep(random.uniform(5, 10))  # there was nothing to do - we can sleep longer
                    continue

            if ctest:
                try:
                    # bierzemy plugina
                    plugin = PLUGINS[ctest.testname]()
                except KeyError:
                    log.exception('Could not find plugin: %s' % ctest.testname)
                    break

                log.debug('Starting scanner plugin: %s' % plugin)

                try:
                    # uruchamiamy i czekamy na status
                    plugin_status = plugin.run(ctest)
                    ctest.status = plugin_status if plugin_status else STATUS.success

                    log.debug('Scanner plugin(%s) for test (%r) finished.' % (plugin.name, ctest))
                except  Exception as error:
                    log.exception('Plugin execution failed: %s' % error)
                    ctest.status = STATUS.exception

                ctest.finish_date = datetime.utcnow()
                ctest.save()

            else:
                sleep(random.uniform(2, 10))  # there was nothing to do - we can sleep longer
        except  Exception as error:
            log.exception('Command run ended with exception: %s' % error)
            #give admins some time
            sleep(30)


def cleaner():
    '''
    Cleaner process, removes unused downloaded data
    '''
    log = logging.getLogger('webscanner.worker.cleaner')
    log.debug("Starting new cleaner pid=%s" % os.getpid())
    sleep(random.uniform(0, 5))

    while(True):
        try:
            dtest = Tests.objects.filter(download_status=STATUS.success, is_deleted=False)[:1]
        except Exception:
            log.exception('Error while fetching tests for cleaning.')
            sleep(random.uniform(3, 5))
            continue
        try:
            if dtest:
                dtest = dtest[0]
                log.debug("Cleaning time! %r" % dtest)
                if dtest.is_done():
                    dtest.clean_private_data()
            else:
                log.debug('Nothing to clean')
                sleep(random.uniform(10, 30))
        except Exception:
            log.exception('Error while cleaning %r.' % dtest)


def downloader():
    log = logging.getLogger('webscanner.worker.downloader')
    log.debug("Starting new downloader pid=%s" % os.getpid())
    sleep(random.uniform(0, 5))

    #main program loop
    while(True):
        try:
            #log.debug('Try to fetch some fresh stuff')
            try:
                with transaction.commit_on_success():
                    test = Tests.objects.filter(download_status=STATUS.waiting)[:1].get()

                    #this should dissallow two concurrent workers for the same commandqueue object
                    testschanged = Tests.objects.filter(download_status=STATUS.waiting).filter(pk=test.pk).update(download_status=STATUS.running)

                    if (testschanged == 0):
                        log.debug("Someone already is downloading this ctest(%r)" % test)
                        test = None
                        sleep(random.uniform(2, 10))  # there was nothing to do - we can sleep longer
                        continue

                    test.download_status = STATUS.running
                    test.download_path = test.private_data_path
                    test.save()
                    log.info('Downloading website %s for %r to %s' % (test.url, test, test.download_path))

            except Tests.DoesNotExist:
                test = None
                log.debug("No Tests in DownloadQueue to process, sleeping.")
                sleep(random.uniform(5, 10))  # there was nothing to do - we can sleep longer
                continue

            if test:
                domain = test.url
                wwwdomain = urlparse.urlparse(test.url).scheme + "://www." + urlparse.urlparse(test.url).netloc + urlparse.urlparse(test.url).path
                os.makedirs(test.download_path)
                cmd = PATH_HTTRACK + " --clean --referer webcheck.me -I0 -r2 --max-time=160 -%%P 1 --preserve --keep-alive -n --user-agent wh-webscanner -s0 -O %s %s %s +*" % (str(test.download_path), wwwdomain, domain)

                args = shlex.split(cmd)
                p = subprocess.Popen(args,  stdout=subprocess.PIPE)
                (stdoutdata, stderrdata) = p.communicate()

                #if p.returncode != 0:
                    #test.download_status = STATUS.exception
                    #test.save()
                    #log.exception("%s returned %s errorcode, strerr: %s"%(PATH_HTTRACK,p.returncode,stderrdata))
                    #raise RuntimeError("%s returned %s errorcode"%(PATH_HTTRACK,p.returncode) )

                test.download_status = STATUS.success
                test.save()
                log.info('Downloading website %s (%r) finished' % (test.url, test))
            else:
                sleep(random.uniform(2, 10))  # there was nothing to do - we can sleep longer
        except  Exception as error:
            log.exception('Downloading ended with an exception: %s' % error)
            #give admins some time
            sleep(30)


if __name__ == '__main__':
    pool = Pool(processes=max([3, cpu_count()]))

    pool.apply_async(cleaner)
    for x in xrange(0, cpu_count()):
        pool.apply_async(worker)
        pool.apply_async(downloader)

    worker()
