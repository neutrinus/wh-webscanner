# -*- encoding: utf-8 -*-
# Create your views here.
from logging import getLogger
from decimal import Decimal
import furl
from datetime import datetime
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from annoying.decorators import render_to
from annoying.functions import get_object_or_None as gooN
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged
from payments.models import Payment, Coupon
from django.contrib import messages

from account.models import UserProfile
from models import CreditsPricingPlan


log = getLogger('webscanner.%s'%__name__)


@login_required
@render_to('payments/payments.html')
def payments(req):
    coupon = None
    if req.GET.get('coupon',None):
        coupon = Coupon.objects.filter(used=False, code=req.GET.get('coupon',None))[:1]
        if coupon:
            coupon=coupon[0]
            log.debug('User %s (pk:%s) passed valid cupon: %s'%(
                req.user, req.user.pk, req.GET['coupon']))
        else:
            messages.error(req, _('Invalid coupon code!'))
            log.debug('User %s (pk:%s) passed invalid coupon %s'%(
                req.user, req.user.pk, req.GET['coupon']))
            coupon = None

            url = furl.furl(req.get_full_path())
            del url.args['coupon']
            return redirect(str(url))


    if 'plan' in req.POST:
        # find plan selected by the user
        plan = gooN(CreditsPricingPlan, pk=req.POST["plan"])

        if not plan:
            messages.error(req, _('Error during payments processing. Sorry.'))
            log.warning('User %s (pk:%s) wanted to buy pricing plan which not exists (pk:%s) (1337?)'%(
                req.user, req.user.pk, req.POST['plan']))
            return redirect('/')
        if not plan.is_active:
            messages.error(req, _('Error during payments processing. Sorry.'))
            log.warning('User %s (pk:%s) wanted to buy pricing plan which is not allowed (pk:%s) (1337?)'%(
                req.user, req.user.pk, req.POST['plan']))
            return redirect('/')

        log.debug("pricing plan selected: %s (pk:%s)"%(plan, plan.pk))
        log.debug("coupon used: %s"%coupon)

        # create transaction for user
        payment = Payment.make_from_pricing_plan(req.user, plan, coupon)
        # WARNING: coupon waits for paypal signal
        payment.save()

        # safety check for free coupons
        if payment.price < Decimal("0.01"):  # minimal paypal amount is 0.01
            log.info('user %s (pk:%s) just bought plan pk=%s for 0.0$'%(
                req.user, req.user.pk, plan.pk))

            payment.price = Decimal("0")
            payment.set_paid()
            payment.save()

            coupon.set_used()
            coupon.save()

            profile = req.user.userprofile
            profile.credits += plan.credits
            profile.save()

            #TODO: pluralize gettext
            messages.info(req, _("You just got %d free credits!")%plan.credits)
            return redirect(req.path)

        log.info("Build form for plan %s and build paypal form"%plan)
        return {'TEMPLATE': 'payments/paypal_redirection.html',
                'paypal_form': payment.render_paypal_form(req),
        }
    pricing_plans = list(CreditsPricingPlan.objects.filter(is_active=True).order_by('credits'))
    if coupon:
        for plan in pricing_plans:
            plan.new_price = coupon.discount_price(plan.price)

    return dict(
        # current coupon
        coupon=coupon,
        payments=req.user.payment_set.filter(is_paid=True).order_by('-date_created'),
        pricing_plans=pricing_plans,
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

    payment.set_paid()
    payment.save()

    if payment.coupon:
        log.info("Coupon code %s has been used by user %s" % (payment.coupon.code, payment.user))
        if payment.coupon.used:
            log.error("It was already used by someone else. Fraud warning!")
        coupon = payment.coupon
        coupon.set_used()
        coupon.save()

    log.info("User %s has paid at price %s" % (payment.user, payment.price))

    #if sub.price != pay.price:
        #log.error("Payment price is different than subscription price. Fraud warning!")

    #send_mail('Tariff changed', Template(open('./tariff.txt').read()).render(Context({'user':u})), settings.DEFAULT_FROM_EMAIL, [user.user.email], fail_silently=False)

def payment_flagged(sender, **kwargs):
    log.warning("Paypal flagged transaction %s, please investigate!" % sender.invoice )

payment_was_successful.connect(payment_ok)
payment_was_flagged.connect(payment_flagged)
