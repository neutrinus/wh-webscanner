# -*- encoding: utf-8 -*-
# Create your views here.
import os
import random
from decimal import Decimal, getcontext
from datetime import datetime as dt, timedelta as td
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from logging import getLogger

from annoying.decorators import render_to
from annoying.functions import get_object_or_None as gooN

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.forms import PayPalEncryptedPaymentsForm
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged

from payments.models import Transaction, Coupon
from django.contrib import messages
from settings import PRODUCT_PRICE

SITE_NAME = Site.objects.get_current()
log= getLogger(__name__)

def make_form(d):
    t = PayPalPaymentsForm
    #if getattr(settings,'PAYPAL_ENCRYPTED',False):
        #t=PayPalEncryptedPaymentsForm
    form = t(initial = d)
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
            coupon = False
    else:
        coupon = None

    print SITE_NAME

    # set Decimal calculation precision
    getcontext().prec = 3
    price = PRODUCT_PRICE - PRODUCT_PRICE*Decimal(coupon.percent)/Decimal("100.0")  if coupon else PRODUCT_PRICE
    if price < Decimal("0"): price = Decimal("0")

    t=Transaction(
        user=req.user,
        type='paypal',
        price=price,
        coupon = coupon if coupon else None,
    )
    t.save()

    return dict(
        transactions = Transaction.objects.filter(user = req.user).order_by('-creation_date'),
        coupon = coupon,
        price = price,
        paypal =
            make_form(dict(
            bussiness = settings.PAYPAL_RECEIVER_EMAIL,
            item_name = "Item name",
            item_number = 1,
            invoice = "%s"%t.code,
            cmd = "_xclick-subscriptions",
            a3 = price ,                      # monthly price
            p3 = 1,                           # duration of each unit (depends on unit)
            t3 = "M",                         # duration unit ("M for Month")
            src = "1",                        # make payments recur
            sra = "1",                        # reattempt payment on payment error
            no_note = "1",                    # remove extra notes (optional)
            notify_url = "%s%s" %(SITE_NAME, reverse('paypal-ipn')),
            return_url = "%s%s" %(SITE_NAME, reverse('payments_paypal_return')),
            cancel_return = "%s%s" %(SITE_NAME, reverse('payments_paypal_cancel')),
        ))
        ,
    )


@csrf_exempt
@render_to('payments/paypal_return.html')
def paypal_return(req):
    return {
        'msg':_("Transakcja zakończona powodzeniem. Dziękujemy.")
    }

@csrf_exempt
@render_to('payments/paypal_cancel.html')
def paypal_cancel(req):
    return {
        'msg':_("Transakcja anulowana")
    }


# signals
def payment_ok(sender, **kwargs):
    print'------ paypal ok -----------'
    ipn=sender
    print 'paypal invoice',ipn.invoice
    try:
        t=gooN(Transaction,code=ipn.invoice)
        if not t:
            print 'error: not transaction in db: %s'%ipn.invoice
            return
        print 'db transaction',t,t.code
        u=gooN(User,pk=t.user.pk)
        if not u:
            print 'error: not user %s in db'%t.user
            return
        print 'db paypal user',u
        if t and t.done():
            p=u.get_profile()
            p.tariff_def = t.tariff_def
            p.expiration_date = dt.now() + td(days=t.tariff_def.duration)
            p.save()
            t.save()
            log.info('transaction %s OK!'%t.code)
            send_mail('Tariff changed', Template(open('./tariff.txt').read()).render(Context({'user':u})), settings.DEFAULT_FROM_EMAIL, [user.user.email], fail_silently=False)

            return
        else:
            log.error('error: transaction %s FAILED but cash go '%t.code)

    except Exception as e:
        log.error('error %s'%e)


def payment_flagged(sender, **kwargs):
    print'------ paypal flagged -----------'
    return payment_ok(sender, **kwargs)

payment_was_successful.connect(payment_ok)
payment_was_flagged.connect(payment_flagged)
