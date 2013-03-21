# -*- encoding: utf-8 -*-

import emails
import signals

# evil monkeypatching
from django.contrib.auth.models import User
User.__unicode__ = lambda self: self.email
User.__repr__ = lambda self: '<User pk:{} email:{}>'.format(self.pk, self.email.encode('utf-8', 'backslashreplace') if self.email else '<Not set!>')

# more evil monkeypatching
from django.utils.functional import SimpleLazyObject
SimpleLazyObject.__repr__ = lambda self: '<SimpleLazyObject: {!r}>'.format(self._wrapped)
