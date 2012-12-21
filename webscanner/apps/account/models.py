from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from annoying.fields import AutoOneToOneField


class UserProfile(models.Model):
    class NotEnoughCredits(Exception):
        def __init__(self, user_has, operation_requires, operation_description):
            self.user_has = user_has
            self.operation_requires = operation_requires
            self.operation_description = operation_description
        def __repr__(self):
            return '<NotEnoughCredits has:%s needed:%s desc:%s>'%(self.user_has,
                self.operation_requires, unicode(self.operation_description))

    user                = AutoOneToOneField(User)
    is_first_login      = models.BooleanField(default=True)
    credits             = models.IntegerField(default=10)


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])
