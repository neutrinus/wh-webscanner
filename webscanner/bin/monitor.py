#! /usr/bin/env python
# -*- coding: utf-8 -*-


from django.core.management import setup_environ
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(os.path.join(os.path.dirname(__file__), './'))

import webscanner.settings
setup_environ(webscanner.settings)

from datetime import datetime, timedelta
from django.conf import settings
import logging


from django.core.mail import EmailMessage
from webscanner.apps.scanner.models import Tests, CommandQueue, STATUS, PLUGINS


time_between_restarts = timedelta(seconds=(12 * 60))
commands = CommandQueue.objects.filter(status=STATUS.running, run_date__lt=datetime.utcnow() - time_between_restarts)

txt = ""

for command in commands:
	txt += "#%s:%s:%s# " %(command.test.domain(), command.testname, command.run_date )


email = EmailMessage(subject='Webcheck long commands monitor' ,
	body=txt,
	from_email=settings.DEFAULT_FROM_EMAIL,
	to=('neutrinus@plusnet.pl',))

email.send()

