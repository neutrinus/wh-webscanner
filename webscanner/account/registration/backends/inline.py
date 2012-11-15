import logging

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
        self.cleaned_data['password1'] = 'TODO:generate_something'
        return self.cleaned_data


class InlineBackend(DefaultBackend):

    log = logging.getLogger(__name__)

    def register(self, request, **cleaneddata):
        self.log.debug('inline registration start')
        signed_url = request.GET.get('u',None)
        if not signed_url:
            messages.error(_("Invalid URL was passed. Please try again!"))
            self.log.error('Invalid signed URL during inline registration')
            return redirect('/')
        signed_url = request.GET.get('u',None)
        url, group_codes = Tests.unsign_url(signed_url)

        self.log.info('creating user inline: %s (url:%s)'%(cleaneddata, url))

        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(cleaneddata['username'],
                                                                    cleaneddata['email'],
                                                                    cleaneddata['password1'],
                                                                    site,
                                                                    send_email=False)
        self.log.info('creating test: %s' % url)
        test = Tests.objects.create(url=url,
                             user=new_user,
                             user_ip=request.META['REMOTE_ADDR'])
        test.start(test_groups=group_codes)

        # send email manually
        profile = new_user.registrationprofile_set.all()[0] 
        profile.send_activation_email_inline(site, new_user, cleaneddata['password1'])

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def activate(self, request, **kwargs):
        import sys
        print >>sys.stderr, 'activate'
        print 'activate'
        raise Exception('witaj')

    def get_form_class(self, request):
        return EmailRegistrationInlineForm

    def post_registration_redirect(self, request, user):
        return reverse('registration_complete'), (), {}

    def post_activation_redirect(self, request, user):
        print 'act red'
        pass

