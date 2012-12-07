
from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from registration_email.forms import EmailRegistrationForm


class WCEmailRegistrationForm(EmailRegistrationForm):
    '''web check customized form'''

    def clean_email(self):
        try:
            return super(WCEmailRegistrationForm, self).clean_email()
        except forms.ValidationError:
            raise forms.ValidationError(mark_safe(
                _("A user with that email already exists.")
                + ' <a href="%s">%s</a>' % (
                        reverse('auth_password_reset'),
                        _("Forgot password?"))
            ))

