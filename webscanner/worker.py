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

import logging
log = logging.getLogger('worker_scanner')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('worker_scanner.log')
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
        log.debug('Try to fetch some fresh stuff')
        with transaction.commit_on_success():		
            try:
                ctest = CommandQueue.objects.filter(status = STATUS.waiting).select_related()[:1].get()
                ctest.status = STATUS.running
                ctest.run_date =  datetime.now()
                ctest.save()
                log.debug('Processing %s'%ctest.test.domain)
                
            except CommandQueue.DoesNotExist:
                ctest = None
                log.debug("No Commands in Queue to process, sleeping.")
                
        if ctest:
            try:
                # bierzemy plugina
                plugin = PLUGINS[ ctest.testname ]()
            except KeyError as e:
                log.debug(' ERROR: Could not find plugin: %s'%ctest.testname)
                break
    
            log.debug('Starting scanner process: %s'%plugin)
            
            try:
                # uruchamiamy i czekamy na status
                plugin.run(ctest)

                log.debug('Scanner plugin(%s) for test (%s) finished.'%(plugin.name,ctest))
                
            except  Exception,e:
                print >>sys.stderr, str(datetime.now()) + " Execution failed: " + str(e)
                stdout_value = None
                ctest.status = STATUS.exception
                ctest.save()
                
            
            log.debug('DEBUG: notfication done')
            
            sleep(random.uniform(0,1)) #there was something to do - we can sleep a bit
        else:
            sleep(random.uniform(10,30)) #there was nothing to do - we can sleep longer


if __name__ == '__main__':
    main()
