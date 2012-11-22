# -*- encoding: utf-8 -*-
import logging
import decimal
from decimal import Decimal
decimal.getcontext().prec = 2

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from hashlib import sha256
from random import getrandbits
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime as dt


log = logging.getLogger(__name__)


def make_code(max=20):
    return sha256(str(getrandbits(8*100))).hexdigest()[:max]


class Coupon(models.Model):
    class Meta:
        verbose_name = _("single-use coupon code")
        verbose_name_plural = _("single-use coupon codes")

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
        self.used_date=dt.utcnow()
        self.save()

    def discount_price(self, price):
        '''
        calculate new price after discout with this coupon
        '''
        price = Decimal(price)
        new_price = price - (price * self.percent / Decimal('100.0'))
        return new_price


class Payment(models.Model):
    code                = models.CharField(_(u'Payment id'),
                                        max_length=512,
                                        default=make_code,
                                        primary_key=True)

    user                = models.ForeignKey(User)
    coupon              = models.ForeignKey("Coupon", blank=True, null=True, default=None)

    #: price after discount (real amount that user paid)
    price               = models.DecimalField(_(u'Price'), max_digits=10, decimal_places=2)
    credits             = models.PositiveIntegerField(default=1)
    date_created        = models.DateTimeField(default=dt.utcnow)

    is_paid             =   models.BooleanField(_(u'has been paid'), default=False)
    date_paid           = models.DateTimeField(blank=True, null=True)

    def render_paypal_form(self, request, sandbox=None):
        '''this is `paypal.standard` specific

        This render paypal sandbox if DEBUG or if sandbox is True
        This render encryption form if PAYPAL_ENCRYPTED
        '''
        from paypal.standard.forms import PayPalPaymentsForm
        from paypal.standard.forms import PayPalEncryptedPaymentsForm

        def make_form(d):
            if getattr(settings,'PAYPAL_ENCRYPTED',False):
                form = PayPalEncryptedPaymentsForm(initial = d)
            else:
                form = PayPalPaymentsForm(initial = d)
            return form

        params = dict(
            bussiness = settings.PAYPAL_RECEIVER_EMAIL,
            item_name = _("%d webcheck.me credits")%self.credits,
            item_number = 1,
            amount = self.price,
            quantity = 1,
            custom = "1337",
            invoice = "%s" % self.code,
            notify_url = request.build_absolute_uri(reverse('paypal-ipn')),  # "%s%s" %(site, reverse('paypal-ipn')),
            return_url = request.build_absolute_uri(reverse('payments_paypal_return')),  # "%s%s" %(site, reverse('payments_paypal_return')),
            cancel_return = request.build_absolute_uri(reverse('payments_paypal_cancel')),  # "%s%s" %(site, reverse('payments_paypal_cancel')),
        )

        form = make_form(params)

        if (settings.DEBUG and sandbox is None) or sandbox is True:
            return form.sandbox()
        else:
            return form.render()

    @classmethod
    def make_from_pricing_plan(cls, user, pricing_plan, coupon=None):
        '''
        We cannot set coupon as used here, we have to wait for paypal signal
        '''
        price = coupon.discount_price(pricing_plan.price) if coupon else pricing_plan.price
        payment = cls(user=user,
                      price=price,
                      credits=pricing_plan.credits,
                      coupon=coupon)
        return payment

    def set_paid(self):
        self.is_paid = True
        self.paid_date = dt.utcnow()


class CreditsPricingPlan(models.Model):
    name                = models.CharField(max_length=128)
    price               = models.DecimalField(max_digits=10, decimal_places=2)
    credits             = models.IntegerField()
    is_active           = models.BooleanField(default=False)


