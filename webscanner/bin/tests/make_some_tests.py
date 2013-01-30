#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

import webscanner.settings
setup_environ(webscanner.settings)

from apps.scanner.models import Tests, CommandQueue, User


sites = ['onet.pl','wp.pl','wykop.pl','alexba.eu','o2.pl']
sites = ['http://%s'%x for x in sites]*4

Tests.objects.all().delete()
CommandQueue.objects.all().delete()

u = User.objects.get(pk=1)
u.userprofile.credits=1000
u.userprofile.save()

for site in sites:
    t=Tests(user=u, url=site)
    t.save()
    t.start()

