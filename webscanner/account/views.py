import urlparse
from logs import log
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import ugettext as _


def ulogout(request):
    logout(request)
    messages.success(request, _('You have ben logged-out. We will miss you!'))

    next_page = request.REQUEST.get("next", '')
    print("next: %s"%next_page)
    if next_page:
        netloc = urlparse.urlparse(next_page)[1]
        # Security check -- don't allow redirection to a different host.
        if (netloc and netloc != request.get_host()):
            log.error("URL hacking detected to %s"%(next_page))
            return redirect('/')
        return(redirect(next_page))

    referer = request.META.get('HTTP_REFERER')
    print("referer: %s"%referer)
    if referer:
        netloc = urlparse.urlparse(referer)[1]
        # Security check -- don't allow redirection to a different host.
        if  (netloc and netloc != request.get_host()):
            log.error("URL hacking detected to %s"%(referer))
            return redirect('/')
        return(redirect(referer))

    return redirect('/')


