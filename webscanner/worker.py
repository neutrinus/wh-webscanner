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
import subprocess
import shlex
import HTMLParser
import urllib
import urlparse
import string
import re
from time import sleep
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db.models import Q
from multiprocessing import Pool, cpu_count
from scanner.models import Tests,CommandQueue,STATUS, PLUGINS


from logs import log

PATH_HTTRACK = '/usr/bin/httrack'
from settings import PATH_TMPSCAN


def worker():
    sleep(random.uniform(0,5))
    
    log.debug("Starting new worker pid=%s"%(os.getpid()))
    #main program loop
    while(True):
        try:
            #log.debug('Try to fetch some fresh stuff')
            with transaction.commit_on_success():		
                try:
                    ctest = CommandQueue.objects.filter(status = STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status = STATUS.success) ).order_by('?')[:1].get()
                    
                    #this should dissallow two concurrent workers for the same commandqueue object
                    CommandQueue.objects.filter(status = STATUS.waiting).filter(pk = ctest.pk).update(status=STATUS.running)
                    
                    ctest.status = STATUS.running
                    ctest.run_date =  datetime.now()
                    ctest.save()
                    log.info('Processing command %s(%s) for %s (queue len:%s)'%(ctest.testname,ctest.pk,ctest.test.url,CommandQueue.objects.filter(status = STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status = STATUS.success) ).count() ))
                    
                except CommandQueue.DoesNotExist:
                    ctest = None
                    #log.debug("No Commands in Queue to process, sleeping.")
                    
            if ctest:
                try:
                    # bierzemy plugina
                    plugin = PLUGINS[ ctest.testname ]()
                except KeyError as e:
                    log.error('Could not find plugin: %s'%ctest.testname)
                    break
        
                log.debug('Starting scanner process: %s'%plugin)
                
                try:
                    # uruchamiamy i czekamy na status
                    ctest.status = plugin.run(ctest)
                    log.debug('Scanner plugin(%s) for test (%s) finished.'%(plugin.name,ctest))                    
                except  Exception,e:
                    log.error('Execution failed: %s'%(e))
                    stdout_value = None
                    ctest.status = STATUS.exception
                
                ctest.finish_date =  datetime.now()
                ctest.save()
                
                    
            else:
                sleep(random.uniform(2,10)) #there was nothing to do - we can sleep longer
        except  Exception,e:
            log.error('Command run ended with exception: %s'%e)
            #give admins some time
            sleep(30)            

def downloader():
    sleep(random.uniform(0,5))
  
    log.debug("Starting new downloader pid=%s"%(os.getpid()))
    #main program loop
    while(True):
        try:
            tmppath = PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24))
            #log.debug('Try to fetch some fresh stuff')
            with transaction.commit_on_success():       
                try:
                    test = Tests.objects.filter(download_status = STATUS.waiting).order_by('?')[:1].get()
                    test.download_status = STATUS.running
                    test.download_path = tmppath
                    test.save()
                    log.info('Downloading website %s for test %s to %s'%(test.url,test.pk,tmppath))
                except Tests.DoesNotExist:
                    test = None
                    #log.debug("No Tests in DownloadQueue to process, sleeping.")
                    
            if test:
                domain = test.url
                wwwdomain = urlparse.urlparse(test.url).scheme + "://www." + urlparse.urlparse(test.url).netloc +urlparse.urlparse(test.url).path
                
                cmd = PATH_HTTRACK + " -rN 2 --max-time=240 -%%P 1 --preserve --keep-alive -n --user-agent wh-webscanner -sN 0 -O %s %s %s"%(str(tmppath),wwwdomain,domain)
              
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
                log.info('Downloading website %s finished'%(test.url))

            else:
                sleep(random.uniform(2,10)) #there was nothing to do - we can sleep longer
        except  Exception,e:
            log.error('Command run ended with exception: %s'%e)
            #give admins some time
            sleep(30)
            

if __name__ == '__main__':
    pool = Pool()
    
    for x in xrange(0,cpu_count()):
        pool.apply_async(worker)
        pool.apply_async(downloader)
    
    worker()
    
