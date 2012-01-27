#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../')
sys.path.append('./')


import settings
setup_environ(settings)

import sys
import os
import random
import subprocess
import shlex
from time import sleep
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.models import User
from scanner.models import Tests,CommandQueue,STATUS, PLUGINS
from django.db import transaction
from django.db.models import Q

import logging
log = logging.getLogger('worker')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)

log.addHandler(fh) 
log.addHandler(sh) 


def main(argv=None):
    if argv is None:
        argv = sys.argv

    #main program loop
    while(True):
        try:
            #log.debug('Try to fetch some fresh stuff')
            with transaction.commit_on_success():		
                try:
                    #ctest = CommandQueue.objects.filter(status = STATUS.waiting)[:1].get()
                    ctest = CommandQueue.objects.filter(status = STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status = STATUS.success) ).order_by('?')[:1].get()
                    
                    ctest.status = STATUS.running
                    ctest.run_date =  datetime.now()
                    ctest.save()
                    log.info('Processing command %s(%s) for %s (queue len:%s)'%(ctest.testname,ctest.pk,ctest.test.domain,CommandQueue.objects.filter(status = STATUS.waiting).filter(Q(wait_for_download=False) | Q(test__download_status = STATUS.success) ).count() ))
                    
                except CommandQueue.DoesNotExist:
                    ctest = None
                    log.debug("No Commands in Queue to process, sleeping.")
                    
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
                    ctest.finish_date =  datetime.now()
                    ctest.save()
                    log.debug('Scanner plugin(%s) for test (%s) finished.'%(plugin.name,ctest))                    
                    
                except  Exception,e:
                    log.exception('Execution failed: %s'%(str(e)))
                    stdout_value = None
                    ctest.status = STATUS.exception
                    ctest.finish_date =  datetime.now()
                    ctest.save()
                                    
            else:
                sleep(random.uniform(1,5)) #there was nothing to do - we can sleep longer
        except  Exception,e:
            log.error('Command run ended with exception: %s'%e)
            #give admins some time
            sleep(30)
            
            
if __name__ == '__main__':
    main()
