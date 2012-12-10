from __future__ import absolute_import
import logging

from django.db import models
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


from registration.signals import user_activated
user_activated.connect(send_welcome_email)


from .models import UserProfile

def too_few_credits_check(sender, instance, **kwargs):
    log = logging.getLogger('webscanner.account.send_lowcredits_email')

    # 1. check object was saved before
    # 2. in this case, instance should be UserProfile (from account)
    if not instance.pk or not isinstance(instance, UserProfile):
        return

    try:
        # get needed variables
        userprofile = instance
        old_userprofile = UserProfile.objects.get(pk=instance.pk)

        # We check here that credits changed from + to 0 (or low)
        # This could be done in two ways:
        # 1. assign new value to field and call 'save'
        # 2. using django F('field')-1 expression
        # So both cases are handled here
        if (old_userprofile.credits > 0 and
                (userprofile.credits < 1 or
                 (isinstance(userprofile.credits, models.expressions.ExpressionNode) and
                  userprofile.credits.connector=='-' and
                  userprofile.credits.children[1] > 0))):

            user = userprofile.user
            current_site = Site.objects.get_current()
            pricing_plans=CreditsPricingPlan.objects.filter(is_active=True).order_by('credits')


            template = loader.find_template('account/email/low_credits.html')[0]
            text = template.render(Context({
                    'user':user,
                    'pricing_plans': pricing_plans,
            }))

            user.email_user(_('[%s] Needs a refill' % current_site.domain),
                            text,
                            settings.DEFAULT_FROM_EMAIL,
                            # django does not do that!
                            #headers = {'Reply-To': settings.DEFAULT_SUPPORT_EMAIL}
                            )

            log.info('Low credit level mail sent to user: %s'%(user.email))
    except Exception:
        log.exception("Error sending low credit level mail to user: %s"%(user.email))
        # we make here all errors silence to the user, but we log them


models.signals.pre_save.connect(too_few_credits_check, UserProfile)


