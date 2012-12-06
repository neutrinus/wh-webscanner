import logging
import time
import hashlib

from django.core import signing
from django.conf import settings
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.models import Site, RequestSite


from registration.models import RegistrationProfile
from registration import signals
from registration.backends.default import DefaultBackend
from registration_email.forms import EmailRegistrationForm, generate_username

from scanner.models import Tests

def _send_activation_email(self, site, user, password):
    # it was easier to copy-paste this code than make a fork
    # author of django-registration does not apply pull-request from 2 years
    ctx_dict = {'activation_key': self.activation_key,
                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                'user': user,
                'password': password,
                'site': site}
    subject = render_to_string('registration/activation_email_subject.txt',
                               ctx_dict)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string('registration/activation_email_inline.txt',
                               ctx_dict)

    self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

# monkey patching, yey
RegistrationProfile.send_activation_email_inline = _send_activation_email


class EmailRegistrationInlineForm(EmailRegistrationForm):

    def __init__(self, *a, **b):
        super(EmailRegistrationInlineForm, self).__init__(*a, **b)
        del self.fields['password1']
        del self.fields['password2']


    def clean(self):
        # unique email validation is done in clean_email of base class

        data = self.cleaned_data
        if not 'email' in data:
            return data

        self.cleaned_data['username'] = generate_username(data['email'])
        self.cleaned_data['password1'] = str(hashlib.sha1(str(time.time())).hexdigest())[:10]
        return self.cleaned_data


class InlineBackend(DefaultBackend):

    log = logging.getLogger(__name__)

    def register(self, request, **cleaneddata):
        self.log.debug('inline registration start')
        signed_url = request.GET.get('u',None)
        try:
            self.log.debug('creating inline test during registration (without saving)')
            test = Tests.make_from_signed_url(signed_url, None,
                                              user_ip=request.META['REMOTE_ADDR'])
            self.log.info('test created during inline registration: %r (not saved yet)'%test)
        except signing.BadSignature:
            messages.error(_("Invalid URL was passed. Please try again!"))
            self.log.error('Invalid signed URL during inline registration: %s', signed_url)
            return redirect('/')

        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)

        self.log.info('creating user during inline registration: %s'%(cleaneddata))
        new_user = RegistrationProfile.objects.create_inactive_user(cleaneddata['username'],
                                                                    cleaneddata['email'],
                                                                    cleaneddata['password1'],
                                                                    site,
                                                                    send_email=False)

        test.user = new_user  # set newly created user as test owner
        test.save()

        try:
            test.start()

            # send email manually
            profile = new_user.registrationprofile_set.all()[0]
            profile.send_activation_email_inline(site, new_user, cleaneddata['password1'])

            signals.user_registered.send(sender=self.__class__,
                                         user=new_user,
                                         request=request)
        except Exception as error:
            messages.error(request, _("Sorry, there was some error during registration. Please try again or contact with administrator"))
            self.log.exception('error starting test during inline registration (deleting newly created user: %r), error:%s'%(new_user,error))
            test.delete()
            new_user.delete()
            return None
        return new_user

    '''
    def activate(self, request, **kwargs):
        user = super(InlineBackend, self).activate(request, **kwargs)
        if not user:
            return user
        raise Exception('witaj')
    '''

    def get_form_class(self, request):
        return EmailRegistrationInlineForm

    def post_registration_redirect(self, request, user):
        if not user:
            # this redirects user and show him a message
            return '/', (), {}
        return reverse('registration_complete'), (), {}

    def post_activation_redirect(self, request, user):
        if not user:
            self.log.info('activation failed')
            return None
        # if user was activated, login him and redirect to results
        self.log.info('activation of user (%s)'%user)
        test = user.tests_set.all()[0]
        from django.contrib import auth
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)
        self.log.info('autologin during activation (user:%s)'%user)
        return test, (), {}

