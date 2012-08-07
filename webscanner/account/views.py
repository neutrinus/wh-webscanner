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


#def ulogin(request):

    #if request.method == "POST":
        #username = request.POST['username']
        #password = request.POST['password']

        #user = authenticate(username=username, password=password)
        #if user is not None:
            #if user.is_active:
                #login(request, user)
                #messages.success(request, _('Welcome %s!'%(user)) )
                #return redirect('/')
            #else:
                #messages.error(request, _('Your account is locked, if this is a mistake please contact our support.'))
                #return redirect('/')
        #else:
            ## Return an 'invalid login' error message.
            #messages.error(request, _('Invalid login data. Please try again.'))
            #return render_to_response('login.html', {}, context_instance=RequestContext(request))
    #else:
        #return render_to_response('login.html', {}, context_instance=RequestContext(request))


#def uregister(request):

    #if request.method == "POST":
        #username = request.POST['username']
        #password = request.POST['password']

        #user = authenticate(username=username, password=password)
        #if user is not None:
            #if user.is_active:
                #login(request, user)
                #messages.success(request, _('Welcome %s!'%(user)) )
                #return redirect('/')
            #else:
                #messages.error(request, _('Your account is locked, if this is a mistake please contact our support.'))
                #return redirect('/')
        #else:
            ## Return an 'invalid login' error message.
            #messages.error(request, _('Invalid login data. Please try again.'))
            #return render_to_response('register.html', {}, context_instance=RequestContext(request))
    #else:
        #return render_to_response('register.html', {}, context_instance=RequestContext(request))

