from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from annoying.fields import AutoOneToOneField


class UserProfile(models.Model):
    user                = AutoOneToOneField(User)
    is_first_login      = models.BooleanField(default=True)
    credits             = models.IntegerField(default=10)

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])
