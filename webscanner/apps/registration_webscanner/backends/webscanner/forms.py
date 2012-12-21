import logging

from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.auth.forms import AuthenticationForm

from registration_email.forms import EmailRegistrationForm

log = logging.getLogger(__name__)

class WCEmailRegistrationForm(EmailRegistrationForm):
    '''web check customized form'''

    def clean_email(self):
        log.debug('cleaning email field for registration form')
        try:
            return super(WCEmailRegistrationForm, self).clean_email()
        except forms.ValidationError:
            raise forms.ValidationError(mark_safe(
                _("This email is already registered.")
                + ' <a href="%s">%s</a>' % (
                        reverse('auth_login'),
                        _("Already have an account? Login."))
            ))

