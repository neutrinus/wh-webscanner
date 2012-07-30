from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # This field is required.
    user        = models.OneToOneField(User)

    is_paid     =   models.BooleanField(_(u'has been paid'), default=False)
    #paid_till   =