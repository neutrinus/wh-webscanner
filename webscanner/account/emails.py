from __future__ import absolute_import
import logging

from django.conf import settings
from django.template import Context, loader
from django.utils.translation import ugettext as _


def send_welcome_email(sender, user, request, **kwargs):
    log = logging.getLogger('webscanner.account.send_welcome_email')
    try:
        template = loader.find_template('account/email/welcome.html')[0]
        text = template.render(Context({'user':user}))
        user.email_user(_('[https://webcheck.me] Welcome'), text, "support@webcheck.me")
        log.info('Welcome mail sent to user: %s'%(user.email))
    except Exception:
        log.exception('Error sending welcome mail to user: %s'%(user.email))
        # we make here all errors silence to the user, but we log them


from registration.signals import user_activated
user_activated.connect(send_welcome_email)
