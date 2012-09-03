import urlparse
import os
from settings import DEFAULT_FROM_EMAIL

from logs import log
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.sites.models import get_current_site
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.template import Template, Context

from settings import DEFAULT_FROM_EMAIL


def ulogout(request):
    logout(request)
    messages.info(request, _('You have ben logged-out. We will miss you!'))

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

def welcome_email(sender, user, request, **kwargs):
    template = Template(open(os.path.join(os.path.dirname(__file__),'templates/account/welcome.html')).read())
    text = template.render(Context({'user':user}))

    send_mail(_('Welcome at webcheck.me!'), text, DEFAULT_FROM_EMAIL, [ user.email ] )


from registration.signals import user_activated
user_activated.connect(welcome_email)
