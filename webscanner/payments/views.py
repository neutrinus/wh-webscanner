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
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged, subscription_signup, recurring_payment, subscription_cancel, subscription_eot
from payments.models import Subscription, Payment, Coupon
from django.contrib import messages
from settings import PRODUCT_PRICE, STATIC_URL

from account.models import UserProfile

SITE_NAME = Site.objects.get_current()

log = getLogger('plugin')

def make_form(d):
    t = PayPalPaymentsForm
    #if getattr(settings,'PAYPAL_ENCRYPTED',False):
        #t=PayPalEncryptedPaymentsForm
    form = t(initial = d)
    return form.sandbox()
    #if getattr(settings,'DEBUG', False):
        #return form.sandbox()
    #else:
        #return form.render()

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

    # get empty subscription or reuse old one
    subscription = Subscription.objects.get_or_create(user = req.user, date_subscribed = None, price = price, coupon = coupon )[0]
    subscription.save()

    return dict(
        payments = Payment.objects.filter(subscription__user = req.user).order_by('-date_created'),
        subscription = subscription,
        coupon = coupon,
        price = price,
        paypal =
            make_form(dict(
            bussiness = settings.PAYPAL_RECEIVER_EMAIL,
            item_name = _("webcheck.me VIP membership"),
            item_number = 1,
            custom = "1337",
            invoice = "%s" % subscription.code,
            cmd = "_xclick-subscriptions",
            a3 = price ,                      # monthly price
            p3 = 1,                           # duration of each unit (depends on unit)
            t3 = "W",                         # duration unit ("M for Month")
            src = "1",                        # make payments recur
            sra = "1",                        # reattempt payment on payment error
            no_note = "1",                    # remove extra notes (req)
            image_url = "%s%s%s" %(SITE_NAME, STATIC_URL, 'paypal_logo.gif'  ),
            notify_url = "%s%s" %(SITE_NAME, reverse('paypal-ipn')),
            return_url = "%s%s" %(SITE_NAME, reverse('payments_paypal_return')),
            cancel_return = "%s%s" %(SITE_NAME, reverse('payments_paypal_cancel')),
        ))
        ,
    )

@csrf_exempt
def paypal_return(req):
    messages.success(req, _('Your payment is finished, thank you! Please wait few seconds till payment is processed'))
    return redirect(reverse('payments_payments'))

@csrf_exempt
def paypal_cancel(req):
    messages.error(req, _('Your payment has been canceled!'))
    return redirect(reverse('payments_payments'))

# signals
def signup(sender, **kwargs):
    log.debug("Subscription signup")

    sub = gooN(Subscription, code = sender.invoice)
    if not sub:
        log.error("Coudn't find subscription for invoice %s" % sender.invoice )
        return

    sub.date_subscribed = datetime.now()
    sub.is_subscribed = True
    sub.save()

    if sub.coupon:
        log.info("Coupon code %s has been used by user %s" % (sub.coupon.code, sub.user))
        if sub.coupon.used:
            log.error("It was already used by someone else. Fraud warning!")
        sub.coupon.set_used()

    log.info("User %s has subscribed at price %s" % (sub.user, sub.price))

def sub_cancel(sender, **kwargs):
    log.debug("Subscription cancel")

    sub = gooN(Subscription, code = sender.invoice)
    if not sub:
        log.error("Coudn't find subscription for invoice %s" % sender.invoice )
        return

    sub.date_canceled = datetime.now()
    sub.is_subscribed = False
    sub.save()
    log.info("User %s has unsubscribed code=%s" % (sub.user, sub.code))

def sub_eot(sender, **kwargs):
    log.debug("Subscription eot")

    sub = gooN(Subscription, code = sender.invoice)
    if not sub:
        log.error("Coudn't find subscription for invoice %s" % sender.invoice )
        return

    sub.date_eot = datetime.now()
    sub.is_subscribed = False
    sub.save()
    log.info("%s's subscription has reach it's EOT code=%s" % (sub.user, sub.code))

    user_profile =  UserProfile.objects.get_or_create(user = sub.user)[0]
    user_profile.paid_till_date = datetime.now()
    user_profile.save()

def payment_ok(sender, **kwargs):
    log.debug("Payment OK")
    sub = gooN(Subscription, code = sender.invoice)
    if not sub:
        log.error("Coudnt find subscription for invoice %s" % sender.invoice )
        return

    # create new payment
    pay = Payment(subscription = sub, price = sender.mc_gross)
    pay.save()
    log.info('Payment: user=%s price=%s invoice=%s' % (sub.user, pay.price, sub.code))

    user_profile =  UserProfile.objects.get_or_create(user = sub.user)[0]
    user_profile.paid_till_date = datetime.now() + td(weeks=1)
    user_profile.save()

    if sub.price != pay.price:
        log.error("Payment price is different than subscription price. Fraud warning!")

    #send_mail('Tariff changed', Template(open('./tariff.txt').read()).render(Context({'user':u})), settings.DEFAULT_FROM_EMAIL, [user.user.email], fail_silently=False)

def payment_flagged(sender, **kwargs):
    log.warning("Paypal flagged transaction %s, please investigate!" % sender.invoice )

payment_was_successful.connect(payment_ok)
payment_was_flagged.connect(payment_flagged)
subscription_signup.connect(signup)
subscription_cancel.connect(sub_cancel)
subscription_eot.connect(sub_eot)
