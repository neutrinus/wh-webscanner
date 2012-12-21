# -*- encoding: utf-8 -*-

import emails
import signals

# monkeypaching
from django.contrib.auth.models import User
User.__unicode__ = lambda self: self.email
User.__repr__ = lambda self: '<User pk:%s email:%s>'%(self.pk, self.email)
