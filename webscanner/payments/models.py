# -*- encoding: utf-8 -*-
from django.db import models
from hashlib import sha256
from random import getrandbits
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from model_utils import Choices
from datetime import datetime as dt, timedelta as td


def make_coupon_code(max=20):
    return sha256(str(getrandbits(8*100))).hexdigest()[:max]

def make_sub_code(max=20):
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
                                             default=make_coupon_code)
    percent             =   models.IntegerField(_(u'Discount size'),
                                                help_text=_(u'Wyrażona w'
                                                u'procentach, przykład: 20'),
                                               )
    used_date           =   models.DateTimeField(default=None,
                                                 blank=True,
                                                 null=True)

    def set_used(self):
        self.coupon.used=True
        self.coupon.used_date=dt.now()
        self.save()

class Subscription(models.Model):

    code                = models.CharField(_(u'Subscription uuid'),
                                        max_length=512,
                                        default=make_sub_code,
                                        unique=True,
                                        primary_key=True)

    user                =   models.ForeignKey(User)
    date_created        =   models.DateTimeField(auto_now_add=True)
    date_subscribed     =   models.DateTimeField(null = True, default = None)
    date_canceled       =   models.DateTimeField(null = True, default = None)
    date_eot            =   models.DateTimeField(null = True, default = None)
    is_subscribed       =   models.BooleanField(_(u'user is subscribed'), default=False)

    price               =   models.DecimalField(_(u'Price'), max_digits=10, decimal_places=2, null = True)
    coupon              =   models.ForeignKey("Coupon",blank=True, null=True, default=None)


class Payment(models.Model):
    subscription        =   models.ForeignKey(Subscription)
    price               =   models.DecimalField(_(u'Price'), max_digits=10, decimal_places=2)
    date_created        =   models.DateTimeField(auto_now_add=True)
    #status
    #idn

    #on save: check if price and sub.price are the same!


