from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime

class UserProfile(models.Model):
    user                = models.OneToOneField(User)
    paid_till_date      =   models.DateTimeField(default=None,blank=1,null=1)

    def is_paid(self):
        if not self.paid_till_date:
            return False

        if datetime.now() > self.paid_till_date:
            return False
        else:
            return True

