
import logging

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from django.contrib import messages

from .models import UserProfile


log = logging.getLogger(__name__)


class FirstLogin(object):
    '''
    If user log in first time, and he has one test (probably added during
    inline registration), redirect him to results.
    '''
    def process_request(self, request):
        if request.user.is_authenticated():
            profile = request.user.userprofile
            if profile.is_first_login:
                profile.is_first_login = False
                profile.save()
                if request.user.tests_set.all().count() == 1:
                    return HttpResponseRedirect(request.user.tests_set.all()[0].get_absolute_url())


class CatchNotEnoughCredits(object):
    '''
    Middleware catch account.models:UserProfile.NotEnoughCredits exception,
    shows user a message (django.contrib.messages) and redirects him to /.
    '''
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

    def process_exception(self, request, exception):
        if not isinstance(exception, UserProfile.NotEnoughCredits):
            return

        self.log.warning('User %r has not enough credits: %r'%(request.user, exception))
        messages.warning(request, _('Not enought credits, please <a href="%s">buy more</a>! You need at least %d.')%(reverse('payments_payments'),exception.operation_requires))
        return HttpResponseRedirect('/')

