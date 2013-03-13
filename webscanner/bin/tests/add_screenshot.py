#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

uuid = sys.argv[1]

import webscanner.settings
setup_environ(webscanner.settings)

from apps.scanner.models import Tests, CommandQueue, User, Results

test = Tests.objects.filter(uuid=uuid)[0]

import random

name = random.choice(uuid)+random.choice(uuid)

item = '''
    <a href="#">
        <img src="http://placehold.it/940x400&text=%s" />
    </a>
    <div class="carousel-caption">
        %s
    </div>
''' % (name, name)
print 'make screenshot for %s - name: %s' % (uuid, name)

Results(test=test, output_desc="witaj", output_full=item, status=0, group=4).save()

print item

