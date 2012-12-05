import logging
import urlparse

from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from django.contrib import messages
#from django.contrib.auth import logout as auth_logout
#from django.contrib.auth.views import login as auth_login_view

from annoying.decorators import render_to

from scanner.models import Tests

def ulogout(request):
    logout(request)
    messages.info(request, _('You have been logged out. We will miss you!'))

'''
def logout(request):
    log = logging.getLogger('%s.ulogout'%__name__)
    messages.info(request, _('You have been logged-out. We will miss you!'))
    return auth_logout(request)
    #return redirect('/')

    # TODO: check sign
    next_page = request.REQUEST.get("next", '')
    if next_page:
        netloc = urlparse.urlparse(next_page)[1]
        # Security check -- don't allow redirection to a different host.
        if (netloc and netloc != request.get_host()):
            log.error("URL hacking detected to %s"%(next_page))
            return redirect('/')
        return(redirect(next_page))

    referer = request.META.get('HTTP_REFERER')
    if referer:
        netloc = urlparse.urlparse(referer)[1]
        # Security check -- don't allow redirection to a different host.
        if  (netloc and netloc != request.get_host()):
            log.error("URL hacking detected to %s"%(referer))
            return redirect('/')
        return(redirect(referer))

    return redirect('/')
'''

