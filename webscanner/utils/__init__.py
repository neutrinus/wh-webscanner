#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import random
import socket
import signal
import errno
import logging
import subprocess
import shlex
import urlparse
from time import sleep
from datetime import datetime, timedelta
#from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import transaction
from django.db.models import Q

import requests
from setproctitle import setproctitle

from webscanner.apps.scanner.models import Tests, CommandQueue, STATUS, PLUGINS


def restarter_process():
    '''
    Restart downloads and CommandQueues after 15 minutes without ending.
    '''
    setproctitle('Worker[restarter]')
    log = logging.getLogger('webscanner.utils.restarter_process')
    TIME_BETWEEN_RESTARTS = 15 * 60  # in seconds
    WAIT_SEC = 30
    time_between_restarts = timedelta(seconds=TIME_BETWEEN_RESTARTS)
    while True:
        # restart downloads
        log.info('Checking for (tests) downloads needs to be restarted.')
        with transaction.commit_on_success():
            tests = Tests.objects.filter(download_status=STATUS.running, download_run_date__lt=datetime.utcnow() - time_between_restarts, is_deleted=False).exclude(download_run_date=None)
            tests_count = tests.count()
            for test in tests:
                log.warning('Downloading for %r is restarting.' % test)
            changed = tests.update(download_status=STATUS.waiting, download_run_date=datetime.utcnow())
            if not tests_count == changed:
                log.warning('Found %s (tests) downloads in running status which should be switched to waiting, but switched only %s' % (len(tests), changed))

        # restart commands
        log.info('Checking for commands needs to be restarted.')
        with transaction.commit_on_success():
            commands = CommandQueue.objects.filter(status=STATUS.running, run_date__lt=datetime.utcnow() - time_between_restarts)
            changed = commands.update(status=STATUS.waiting, run_date=datetime.utcnow())
            for command in commands:
                log.warning('CommandQueue %r is restarting.' % command)
            if not len(commands) == changed:
                log.warning('Found %s commands in running status which should be switched to waiting, but switched only %s' % (len(commands), changed))

        log.debug('Waiting %s seconds' % WAIT_SEC)
        sleep(WAIT_SEC)


def worker_process():
    setproctitle('Worker[process worker]')
    log = logging.getLogger('webscanner.utils.worker_process')
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
                        continue

                    ctest.status = STATUS.running
                    ctest.run_date = datetime.utcnow()
                    ctest.save()
                    log.info('Processing command %s(%s) for %s (queue len:%s)' % (ctest.testname, ctest.pk, ctest.test.url, CommandQueue.objects.filter(status=STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status=STATUS.success)).count()))
                except CommandQueue.DoesNotExist:
                    log.debug("No Commands in Queue to process, sleeping.")
                    sleep(random.uniform(2, 10))
                    continue

            if ctest:
                try:
                    try:
                        # bierzemy plugina
                        plugin = PLUGINS[ctest.testname]()
                    except KeyError:
                        log.exception('Could not find plugin: %s' % ctest.testname)
                        break

                    log.debug('Starting scanner plugin: %s' % plugin)

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


def download_cleaner_process():
    '''
    Cleaner process, removes unused downloaded data
    '''
    setproctitle('Worker[cleaner]')
    log = logging.getLogger('webscanner.worker.cleaner')
    log.debug("Starting new cleaner pid=%s" % os.getpid())
    if not os.path.exists(settings.WEBSCANNER_SHARED_STORAGE):
        raise Exception('Cannot run cleaner, WEBSCANNER_SHARED_STORAGE (%s) does not exist. (this not check it is mounted, only existence)' % settings.WEBSCANNER_SHARED_STORAGE)
    LOCK_FILE = os.path.join(settings.WEBSCANNER_SHARED_STORAGE, '.cleaner_process_running')
    if os.path.exists(LOCK_FILE):
        raise Exception('Lock file (%s) exists, it means cleaner is already running, or was not closed properly. Check content of this file and if you are sure there is no other cleaner process you can remove this file' % LOCK_FILE)

    with open(LOCK_FILE, "a") as f:
        f.write('[cleaner_process:lock:pid=%d]\n' % os.getpid())
        f.write('pid=%s\n' % os.getpid())
        f.write('start_utc=%s\n' % datetime.utcnow())
        f.write('host=%s\n' % socket.gethostname())

    sleep(random.uniform(0, 5))

    MAX_WAITING_TIME = 30 * 60  # max number of seconds after which log.error
                                # should be generated if task has downloaded
                                # data, but is not done (maybe some exceptions
                                # has occurred)
    MIN_TIME_BETWEEN_CHECKS = 1 * 60  # minimum time between the same test
                                      # will be checked again
    # this is cache for tests pk
    # for each test we monitor some parameters:
    # - count: how many times test object was tried to clean
    # - start: first time when was fetched but was not done
    # - last: last time when was fetched but was not done
    # - notified: last time when log.error was generated (probably mail was
    #              sent to admin)
    #
    # if test will be successfully removed, it is also removed from cache
    cache = {}

    try:
        while(True):
            try:
                # TODO: pk__not_in - may be not appropriate when there is huge
                # amount of tests - it should be tested on big DB
                log.debug('db query')
                dtest = Tests.objects.exclude(pk__in=cache.iterkeys()).filter(download_status=STATUS.success, is_deleted=False).order_by('?')[:1]
            except Exception:
                log.exception('Error while fetching tests for cleaning.')
                sleep(random.uniform(3, 5))
                continue
            try:
                if dtest:
                    dtest = dtest[0]
                    if dtest.pk in cache:
                        if (datetime.utcnow() - cache[dtest.pk]['last']).total_seconds() < MIN_TIME_BETWEEN_CHECKS:
                            continue
                    if dtest.is_done():
                        log.info("Cleaning time for %r!" % dtest)
                        dtest.clean_private_data()
                        if dtest.pk in cache:
                            del cache[dtest.pk]
                    else:
                        log.debug('%r is not finished yet.' % dtest)
                        if dtest.pk in cache:
                            cache[dtest.pk]['count'] += 1
                            cache[dtest.pk]['last'] = datetime.utcnow()
                            start_point = cache[dtest.pk]['notified'] if cache[dtest.pk]['notified'] else cache[dtest.pk]['start']
                            if (cache[dtest.pk]['last'] - start_point).total_seconds() > MAX_WAITING_TIME:
                                log.error('%r is not finished yet, but probably it should. It has started at %s and until now is %s seconds. There was %s try/tries of removing it' % (
                                          dtest, cache[dtest.pk]['start'], (datetime.utcnow() - cache[dtest.pk]['start']).total_seconds(), cache[dtest.pk]['count']))
                        else:
                            log.debug('%r added to cache' % dtest)
                            cache[dtest.pk] = {'notified': None,
                                               'start': datetime.utcnow(),
                                               'last': datetime.utcnow(),
                                               'count': 1,
                                               }
                    del dtest
                else:
                    log.debug('Nothing to clean.')
                    sleep(random.uniform(60, 120))

            except Exception:
                log.exception('Error while cleaning %r.' % dtest)
                sleep(random.uniform(10, 20))

    finally:
        if os.path.exists(LOCK_FILE):
            log.info('Removing LOCK_FILE: %s' % LOCK_FILE)
            os.unlink(LOCK_FILE)
        else:
            log.warning('While closing cleaner lack of LOCK_FILE (%s) detected. Someone remove it before exiting cleaner process!' % LOCK_FILE)


def downloader_process():
    setproctitle('Worker[downloader]')
    PATH_HTTRACK = getattr(settings, 'PATH_HTTRACK', '/usr/bin/httrack')
    if not os.path.isfile(PATH_HTTRACK):
        raise Exception('httrack is not installed in %s. Please install it or correct PATH_HTTRACK in `settings`' % PATH_HTTRACK)

    log = logging.getLogger('webscanner.utils.downloader_process')
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
                domain = requests.head(test.url, timeout=5).url
                if not test.download_path:
                    test.download_path = test.private_data_path
                    test.save()
                elif not os.path.exists(test.download_path):
                    os.makedirs(test.download_path)

                cmd = PATH_HTTRACK + " --clean --referer webcheck.me -I0 -r2 --max-time=160 -%%P 1 --preserve --keep-alive -n --user-agent wh-webscanner -s0 -O %s %s +*" % (str(test.download_path), domain)

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
        except Exception as error:
            log.exception('Downloading ended with an exception: %s' % error)
            #give admins some time
            sleep(30)


def process_wrapper(func):
    log = logging.getLogger('%s.process_wrapper' % __name__)
    log.info('Starting process with "%s".' % func.__name__)
    import sys
    try:
        sys.exit(func())
    except KeyboardInterrupt:
        log.info('Process stopped by the user.')
        sys.exit(130)  # 130 - owner died
