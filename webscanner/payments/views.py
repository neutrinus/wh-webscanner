# -*- encoding: utf-8 -*-
# Create your views here.
import os
import random
from decimal import Decimal, getcontext
from datetime import datetime, timedelta as td
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from logging import getLogger
from django.shortcuts import redirect
from annoying.decorators import render_to
from annoying.functions import get_object_or_None as gooN
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.forms import PayPalEncryptedPaymentsForm
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged
from payments.models import Payment, Coupon
from django.contrib import messages
from settings import PRODUCT_PRICE, STATIC_URL

from account.models import UserProfile

SITE_NAME = Site.objects.get_current()

log = getLogger('plugin')

def make_form(d):
    if getattr(settings,'PAYPAL_ENCRYPTED',False):
        form = PayPalEncryptedPaymentsForm(initial = d)
    else:
        form = PayPalPaymentsForm(initial = d)

    if getattr(settings,'DEBUG', False):
        return form.sandbox()
    else:
        return form.render()

@login_required
@render_to('payments/payments.html')
def payments(req):
    if req.GET.get('coupon',None):
        coupon = Coupon.objects.filter(used=False, code=req.GET.get('coupon',None))
        if coupon:
            coupon=coupon[0]
        else:
            messages.error(req, _('Invalid coupon code!'))
            coupon = None
    else:
        coupon = None

    # set Decimal calculation precision
    getcontext().prec = 2
    price = PRODUCT_PRICE - PRODUCT_PRICE*Decimal(coupon.percent)/Decimal("100.0")  if coupon else PRODUCT_PRICE
    if price < Decimal("0"): price = Decimal("0")

    # get empty payment or reuse old one
    payment = Payment.objects.get_or_create(user = req.user, price = price, coupon = coupon, is_paid = False )[0]
    payment.save()

    return dict(
        payments = Payment.objects.filter(user = req.user).order_by('-date_created'),
        payment = payment,
        coupon = coupon,
        price = price,
        paypal =
            make_form(dict(
            bussiness = settings.PAYPAL_RECEIVER_EMAIL,
            item_name = _("webcheck.me scanner fee"),
            item_number = 1,
            amount = price,
            custom = "1337",
            invoice = "%s" % payment.code,
            image_url = "%s%s%s" %(SITE_NAME, STATIC_URL, 'paypal_logo.gif'  ),
            notify_url = "%s%s" %(SITE_NAME, reverse('paypal-ipn')),
            return_url = "%s%s" %(SITE_NAME, reverse('payments_paypal_return')),
            cancel_return = "%s%s" %(SITE_NAME, reverse('payments_paypal_cancel')),
        ))
        ,
    )

@csrf_exempt
def paypal_return(req):
    messages.success(req, _('Your payment is <b>completed</b>, thank you! You will get an email with payment details. Please wait a few seconds while the payment is processed'))
    return redirect(reverse('payments_payments'))


@csrf_exempt
def paypal_cancel(req):
    messages.error(req, _('Your payment has been canceled!'))
    return redirect(reverse('payments_payments'))


def payment_ok(sender, **kwargs):
    log.debug("Payment OK")
    payment = gooN(Payment, code = sender.invoice)
    if not payment:
        log.error("Coudnt find payment for invoice %s" % sender.invoice )
        return
    else:
        log.info('Payment: user=%s price=%s invoice=%s' % (payment.user, payment.price, payment.code))

    user_profile =  UserProfile.objects.get_or_create(user = payment.user)[0]
    user_profile.credits += 100
    user_profile.save()


    payment.date_paid = datetime.now()
    payment.is_paid = True
    payment.save()

    if payment.coupon:
        log.info("Coupon code %s has been used by user %s" % (payment.coupon.code, payment.user))
        if payment.coupon.used:
            log.error("It was already used by someone else. Fraud warning!")
        payment.coupon.set_used()

    log.info("User %s has paid at price %s" % (payment.user, payment.price))


    #if sub.price != pay.price:
        #log.error("Payment price is different than subscription price. Fraud warning!")

    #send_mail('Tariff changed', Template(open('./tariff.txt').read()).render(Context({'user':u})), settings.DEFAULT_FROM_EMAIL, [user.user.email], fail_silently=False)

def payment_flagged(sender, **kwargs):
    log.warning("Paypal flagged transaction %s, please investigate!" % sender.invoice )

payment_was_successful.connect(payment_ok)
payment_was_flagged.connect(payment_flagged)
