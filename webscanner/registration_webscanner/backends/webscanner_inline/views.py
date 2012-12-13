
import logging

from django.core import signing
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import views as auth_views

from registration.views import register

log = logging.getLogger(__name__)

def register_inline(request, backend, success_url=None, form_class=None,
                    disallowed_url='registration_disallowed',
                    template_name='registration/registration_inline.html',
                    extra_context=None):
    '''
    This view needs signed url in `u` GET parameter
    '''
    try:
        signed_url = request.GET.get('u','not valid :(')
        log.debug('signed url from GET[u]: %s'%signed_url)
        org_url = signing.loads(signed_url)
        log.debug('De-signed url: %s'%org_url)
    except signing.BadSignature:
        messages.error(request, _("Passed URL was invalid. Please try again!"))
        log.error('Invalid signed URL passed to inline registration')
        return redirect('/')

    if not extra_context:
        extra_context={}

    extra_context['url']=org_url[0]

    return register(request, backend, success_url, form_class, 
            disallowed_url, template_name, extra_context)

from scanner.models import Tests

def login_inline(request, **kwargs):
    surl = request.GET.get('u', None)

    if surl:
        log.debug('Login inline')
        ret = auth_views.login(request, **kwargs)
        if request.user.is_authenticated():
            log.debug('logged in as %r'%request.user)
            log.debug('make a scan and redirect user')
            test = Tests.make_from_signed_url(surl,
                request.user,
                request.META['REMOTE_ADDR'])
            test.save()
            log.debug('%r was just saved.'%test)
            test.start()
            log.debug('%r was just started.'%test)
            return HttpResponseRedirect(test.get_absolute_url())
        else:
            log.debug('not logged correctly')
        return ret
    else:
        log.debug('Ordinary login')
    return auth_views.login(request, **kwargs)

