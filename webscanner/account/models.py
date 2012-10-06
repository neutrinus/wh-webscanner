from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime

class UserProfile(models.Model):
    user                = models.OneToOneField(User)
    credits             = models.IntegerField(default=10)

