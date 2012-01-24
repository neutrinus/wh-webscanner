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
import HTMLParser
import urllib
import urlparse
import string
import re
import shlex

from time import sleep
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.models import User
from scanner.models import Tests,CommandQueue,STATUS, PLUGINS
from django.db import transaction
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

import logging
log = logging.getLogger('downloader')
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

PATH_TMPSCAN = '/tmp/clamdd/'
PATH_PUF = '/usr/bin/puf'


def main(argv=None):
    if argv is None:
        argv = sys.argv

    #main program loop
    while(True):
        try:
            tmppath = PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(12))
            log.debug('Try to fetch some fresh stuff')
            with transaction.commit_on_success():		
                try:
                    test = Tests.objects.filter(download_status = STATUS.waiting).order_by('?')[:1].get()
                    test.download_status = STATUS.running
                    test.download_path = tmppath
                    test.save()
                    log.info('Downloading website %s for test %s to %s'%(test.domain,test.pk,tmppath))
                    
                except Tests.DoesNotExist:
                    test = None
                    log.debug("No Tests in DownloadQueue to process, sleeping.")
                    
            if test:
                domain = test.domain
                
                log.debug(unicode(_("Downloading webpage")))
                cmd = PATH_PUF + " -U wh-webscanner -xd -xg  -r+ -l 2 -P %s %s"%(str(tmppath),str(domain))
              
                args = shlex.split(cmd)
                p = subprocess.Popen(args,  stdout=subprocess.PIPE)
                (stdoutdata, stderrdata) = p.communicate()

                #print stderrdata
                
                if p.returncode != 0:
                    test.download_status = STATUS.exception
                    test.save()
                    log.exception("%s returned non-0 errorcode, strerr: %s"%(PATH_PUF,stderrdata))
                    raise RuntimeError("%s returned non-0 errorcode"%(PATH_PUF) )
                
                test.download_status = STATUS.success
                test.save()
                log.info('Downloading website %s finished'%(test.domain))

            else:
                sleep(random.uniform(1,5)) #there was nothing to do - we can sleep longer
        except  Exception,e:
            log.error('Command run ended with exception: %s'%e)
            #give admins some time
            sleep(30)
            
            
if __name__ == '__main__':
    main()
