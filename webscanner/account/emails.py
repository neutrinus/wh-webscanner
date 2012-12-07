from __future__ import absolute_import
import logging

from django.conf import settings
from django.template import Context, loader
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from payments.models import CreditsPricingPlan

def send_welcome_email(sender, user, request, **kwargs):
    log = logging.getLogger('webscanner.account.send_welcome_email')
    current_site = Site.objects.get_current()

    try:
        template = loader.find_template('account/email/welcome.html')[0]
        text = template.render(Context({'user':user}))
        user.email_user(_('[%s] Welcome' % current_site.domain),
                        text,
                        settings.DEFAULT_FROM_EMAIL,
                        headers = {'Reply-To': settings.DEFAULT_SUPPORT_EMAIL})

        log.info('Welcome mail sent to user: %s'%(user.email))
    except Exception:
        log.exception('Error sending welcome mail to user: %s'%(user.email))
        # we make here all errors silence to the user, but we log them

def send_lowcredits_email(sender, user, request, **kwargs):
    log = logging.getLogger('webscanner.account.send_lowcredits_email')
    current_site = Site.objects.get_current()
    pricing_plans=CreditsPricingPlan.objects.filter(is_active=True).order_by('credits'),

    try:
        template = loader.find_template('account/email/low_credits.html')[0]
        text = template.render(Context({
                'user':user,
                'pricing_plans': pricing_plans,
        }))

        user.email_user(_('[%s] Needs a refill' % current_site.domain),
                        text,
                        settings.DEFAULT_FROM_EMAIL,
                        headers = {'Reply-To': settings.DEFAULT_SUPPORT_EMAIL})

        log.info('Low credits mail sent to user: %s'%(user.email))
    except Exception:
        log.exception('Error sending low credits mail to user: %s'%(user.email))
        # we make here all errors silence to the user, but we log them



from registration.signals import user_activated
user_activated.connect(send_welcome_email)
