# -*- encoding: utf-8 -*-
from django.db import models
from hashlib import sha256
from random import getrandbits
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from model_utils import Choices
from datetime import datetime as dt, timedelta as td

# Create your models here.

#: Używamy w sposób następujący::
#:
#:      from scanner.models import TRANSACTION_STATUS_TYPE as TST
#:
#:      x = TST.success
TRANSACTION_STATUS_TYPES = Choices(
    (0, 'waiting', _('in progress')),
    (1, 'nomoney', _('not enough money')),
    (2, 'prov_canceled', _('canceled by provider')),
    (3, 'self_canceled', _('canceled by myself')),
    (4, 'canceled', _('canceled by site operator')),
    (5, 'success', _('payed')),
    (6, 'timeout', _('time out for payment')),
)

TRANSACTION_TYPES = Choices(
    ('paypal', 'paypal',_('Paypal') ),
)



def make_coupon_code(max=20):
    return sha256(str(getrandbits(8*100))).hexdigest()[:max]

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


def make_transaction_code():
    return sha256(str(getrandbits(8*512))).hexdigest()

def expdate():
    return dt.now() + td(hours=24)

class Transaction(models.Model):
    class Meta:
        verbose_name = _("Transaction")
    code                = models.CharField(_(u'Transaction uuid'),
                                           max_length=512,
                                           default=make_transaction_code,
                                           unique=True,
                                           primary_key=True)
    user                =   models.ForeignKey(User)
    type                =   models.CharField(max_length=50,
                                             choices = TRANSACTION_TYPES)
    price               =   models.DecimalField(_(u'Price'),
                                                max_digits=10,
                                                decimal_places=2)
    coupon              =   models.ForeignKey("Coupon",blank=True, null=True, default=None)

    status              =   models.IntegerField(choices=TRANSACTION_STATUS_TYPES, default=0)
    creation_date       =   models.DateTimeField(auto_now_add=True)
    modify_date         =   models.DateTimeField(auto_now=True)
    expire_date         =   models.DateTimeField(default=expdate)

    def is_valid(self):
        if self.status == TRANSACTION_STATUS_TYPES.waiting and self.check_timeout():
            return True
        return False

    def check_timeout(self):
        if dt.now() > self.expire_date:
            if self.status == TRANSACTION_STATUS_TYPES.waiting:
                self.status=TRANSACTION_STATUS_TYPES.timeout
                self.save()
            return False
        return True

    def done(self):
        if self.is_valid():
            self.status = TRANSACTION_STATUS_TYPES.success
            return True
        return False

    def save(self,*a,**b):
        if self.coupon and self.status == TRANSACTION_STATUS_TYPES.success and not self.coupon.used:
            self.coupon.used=True
            self.coupon.used_date=dt.now()
        super(Transaction,self).save(*a,**b)
