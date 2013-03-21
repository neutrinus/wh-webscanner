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
from django.db.models import Q
from django.core.mail import EmailMessage
import logging
from webscanner.apps.scanner.models import Tests, CommandQueue, STATUS, PLUGINS


time_between_restarts = timedelta(seconds=(12 * 60))
commands = CommandQueue.objects.filter(Q(status=STATUS.running) | Q(status=STATUS.waiting)).filter( run_date__lt=datetime.utcnow() - time_between_restarts).order_by("run_date")

if commands:
	command = commands[0]
	txt = "%s:%s:%s, %s total " %(command.test.domain(), command.testname, datetime.utcnow() - command.run_date, len(commands) )


	email = EmailMessage(subject='webcheck:' + txt ,
		body=command.test.uuid,
		from_email=settings.DEFAULT_FROM_EMAIL,
		to=('neutrinus@plusnet.pl',))

	email.send()

