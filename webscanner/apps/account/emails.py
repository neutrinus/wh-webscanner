from __future__ import absolute_import
import logging

from django.db import models
from django.conf import settings
from django.template import Context, loader
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from payments.models import CreditsPricingPlan


def send_welcome_email(sender, user, request, **kwargs):
    """
    After successfull activation user gets a welcome email
    """
    log = logging.getLogger('webscanner.account.send_welcome_email')
    try:
        template = loader.find_template('account/email/welcome.html')[0]
        text = template.render(Context({'user': user,
                                        'site': Site.objects.get_current()}))
        email = EmailMessage(subject='%s %s' % (settings.EMAIL_SUBJECT_PREFIX, _('Welcome')),
                             body=text,
                             from_email=settings.DEFAULT_FROM_EMAIL,
                             to=[user.email],
                             headers={'Reply-To': settings.DEFAULT_SUPPORT_EMAIL})
        email.send()

        log.info('Welcome mail sent to user: %r' % user)
    except Exception:
        log.exception('Error sending welcome mail to user: %r' % user)
        # we make here all errors silence to the user, but we log them


from registration.signals import user_activated
user_activated.connect(send_welcome_email, dispatch_uid='send_welcome_email_after_account_activation')


from .models import UserProfile


def too_few_credits_check(sender, instance, **kwargs):
    '''
    This function sends mail to user if the credits level goes down.
    Tested only as pre_save signal for UserProfile model!

    If this function is called as signal, `instance`.credits is unsaved yet,
    and can be integer or ExpressionNode (django F query).
    '''
    log = logging.getLogger('webscanner.account.send_lowcredits_email')

    # 1. check object was saved before
    # 2. in this case, instance should be UserProfile (from account)
    if not instance.pk or not isinstance(instance, UserProfile):
        return

    try:
        # get needed variables
        userprofile = instance
        old_userprofile = UserProfile.objects.get(pk=instance.pk)

        log.debug('userprofile updated. credits: %s -> %s' % (old_userprofile.credits,
                                                              userprofile.credits))
        # We check here that credits changed from + to 0 (or low)
        # This could be done in two ways:
        # 1. assign new value to field and call 'save'
        # 2. using django F('field')-1 expression
        # So both cases are handled here

        def check_move(old, new, to_value=0):
            '''
            :param old: old value
            :type old: integer
            :param new: new value (new value can be integer or ExpressionNode)
            :type new: integer or ExpressionNode
            :param to_value: new value == to_value -> true
            :type to_value: integer

            :returns: whether value changed with conditions (old>new and new==to_value)
            '''
            # checks of argument types
            if not isinstance(old, int) or not isinstance(to_value, int):
                log.error('`old` (%s) or `to_value`(%s) is not int!' % (old, to_value))
                return False

            if isinstance(new, int):
                # we want only old > new
                if not old > new:
                    return False
                if new == to_value:
                    return True
                return False

            elif isinstance(new, models.expressions.ExpressionNode):
                # here it is checked, that credits field is applied by F('credits')-x

                if not new.connector == '-':
                    # we assume only F('credits') - x (subtration)
                    return False

                if not isinstance(new.children[1], int):
                    # we assume x in F('credits')-x is int
                    return False

                if not new.children[1] > 0:
                    # F('credits') - 0 is not our case :)
                    return False

                new_value = int(old - new.children[1])
                if new_value == to_value:
                    return True

                return False

            else:
                log.error('`new` is not int nor ExpressionNode (new:%s)' % new)
                return False

            log.error('assertion')
            return False

        if (check_move(old_userprofile.credits, userprofile.credits, to_value=5) or
            check_move(old_userprofile.credits, userprofile.credits, to_value=0)):
            log.info('sending mail to %r: low credits (current value: %s)' % (userprofile.user, userprofile.credits))

            user = userprofile.user
            pricing_plans = CreditsPricingPlan.objects.filter(is_active=True).order_by('credits')

            template = loader.find_template('account/email/low_credits.html')[0]
            text = template.render(Context({'user': user,
                                            'site': Site.objects.get_current(),
                                            'pricing_plans': pricing_plans}))

            email = EmailMessage(subject='%s %s' % (settings.EMAIL_SUBJECT_PREFIX, _('Needs a refill')),
                                 body=text,
                                 from_email=settings.DEFAULT_FROM_EMAIL,
                                 to=[user.email],
                                 headers={'Reply-To': settings.DEFAULT_SUPPORT_EMAIL})
            email.send()

            log.info('Low credit level mail sent to user: %r' % user)
    except Exception:
        # we make here all errors silence to the user, but we log them
        log.exception("Error sending low credit level mail to user: %r" % user)


models.signals.pre_save.connect(too_few_credits_check, UserProfile, dispatch_uid='send_mail_when_credits_level_is_low_signal')
