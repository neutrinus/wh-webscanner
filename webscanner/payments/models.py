# -*- encoding: utf-8 -*-
from django.db import models
from hashlib import sha256
from random import getrandbits
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from model_utils import Choices
from datetime import datetime as dt, timedelta as td


def make_code(max=20):
    return sha256(str(getrandbits(8*100))).hexdigest()[:max]

def expdate():
    return dt.now() + td(hours=24)

class Coupon(models.Model):
    class Meta:
        verbose_name = _("one-use coupon code")

    used                =   models.BooleanField(_(u'has been used'), default=False)
    code                =   models.CharField(_(u'code'),
                                             max_length=256,
                                             unique=True,
                                             default=make_code)
    percent             =   models.IntegerField(_(u'Discount size'),
                                                help_text=_(u'in percent! ex: 20'),
                                               )
    used_date           =   models.DateTimeField(default=None,
                                                 blank=True,
                                                 null=True)
    def set_used(self):
        self.used=True
        self.used_date=dt.now()
        self.save()


class Payment(models.Model):
    user                = models.ForeignKey(User)
    coupon              = models.ForeignKey("Coupon",blank=True, null=True, default=None)

    price               = models.DecimalField(_(u'Price'), max_digits=10, decimal_places=2)
    date_created        = models.DateTimeField(auto_now_add=True)
    date_paid           = models.DateTimeField(auto_now_add=True)

    code                = models.CharField(_(u'Payment uuid'),
                                        max_length=512,
                                        default=make_code,
                                        unique=True,
                                        primary_key=True)

    is_paid             =   models.BooleanField(_(u'has been paid'), default=False)


