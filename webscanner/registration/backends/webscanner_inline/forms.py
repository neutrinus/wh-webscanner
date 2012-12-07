import time
import hashlib
import logging

from django.utils.translation import ugettext as _

from registration.backends.webscanner.forms import WCEmailRegistrationForm
from registration_email.forms import  generate_username

log = logging.getLogger(__name__)

class WCEmailRegistrationInlineForm(WCEmailRegistrationForm):

    def __init__(self, *a, **b):
        super(WCEmailRegistrationInlineForm, self).__init__(*a, **b)
        del self.fields['password1']
        del self.fields['password2']

    def clean(self):
        # unique email validation is done in clean_email of base class
        if not 'form:registration_inline' in self.data:
            log.debug('not cleaning register inline form')
            return None
        log.debug('cleaning register inline form')

        data = self.cleaned_data
        if not 'email' in data:
            return data

        self.cleaned_data['username'] = generate_username(data['email'])
        self.cleaned_data['password1'] = self._generate_password()
        return self.cleaned_data

    def _generate_password(self):
        return str(hashlib.sha1(str(time.time())).hexdigest())[:10]

