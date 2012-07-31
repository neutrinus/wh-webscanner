# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.views.generic.list_detail import object_list
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.db.models import Q, Max
from django.contrib.comments.models import Comment
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.sitemaps import ping_google
from django.contrib.auth import logout, authenticate, login
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from urlparse import urlparse
from datetime import datetime
from annoying.decorators import render_to
import json
from logs import log
from scanner.models import *

def index(request):
	return render_to_response('scanner/index.html', {}, context_instance=RequestContext(request))

@render_to('terms.html')
def terms(request):
    return dict()

@render_to('about.html')
def about(request):
    return dict()

@render_to('contact.html')
def contact(request):
    return dict()

@render_to('pricing.html')
def pricing(request):
    return dict()


@login_required
@render_to('scanner/scan_archive.html')
def scan_archive(request):
    """ Presents user his scans archive """

    return dict(
        tests = Tests.objects.filter(user = request.user).order_by('-creation_date'),
    )


def results(request):
    """ page with scann results """
    if request.method == 'POST':
        url = request.POST.get("url")

        #basic url validiation
        if not urlparse(url).scheme:
            url = "http://"+url
        if (urlparse(url).scheme not in ["http","https"]) or \
           (not urlparse(url).netloc) or \
           len(urlparse(url).netloc) < 3:
            messages.warning(request, _('Invalid website address (URL), please try again.'))
            return redirect('/')

        if request.user.is_authenticated():
            test = Tests(url=url, user=request.user, priority=20)
        else:
            test = Tests(url=url)
        test.save()

        log.debug("User ordered report for url:%s, report_uuid:%s"%(url,test.uuid))

        # order all posible commands
        for testname,plugin in TESTDEF_PLUGINS:
            oplugin = PLUGINS[ testname ]()
            a = CommandQueue(test=test, testname = testname, wait_for_download = oplugin.wait_for_download )
            a.save()

        #TODO: please dont hardcode urls..
        return redirect('/reports/'+ test.uuid)
    else:
        return redirect(reverse('scanner_index'))

def show_report(request, uuid):
    #messages.info(request, 'Three credits remain in your account.')
    #messages.success(request, 'Profile details updated.')
    #messages.warning(request, 'Your account expires in three days.')
    #messages.error(request, 'Document deleted.')
    #get_object_or_404 ?

    try:
        test = Tests.objects.filter(uuid=uuid).get()
    except ObjectDoesNotExist:
        return redirect('/')

    return render_to_response('scanner/results.html', {'test': test}, context_instance=RequestContext(request))

def check_results(request, uuid):
    """
    ajax requests handler - suply information about tests
    """
    test = Tests.objects.filter(uuid=uuid).get()

    last = request.GET.get("last")
    if not last:
        last=0

    results = Results.objects.filter(test=test).filter(pk__gt = last)

    foo = []
    for result in results:
        foo.append({'output_desc':result.output_desc,
                    'output_full':result.output_full,
                    'status': result.status,
                    'importance': result.importance,
                    'id': result.pk,
                    'group': result.group})

    data = {    'ordered': test.commands_count() + 1,
                "done": test.commands_done_count() + 1,
                "test_duration": test.duration(),
                "results": foo,
    }

    return HttpResponse('%s(%s)'%(request.GET.get('callback',''),  json.dumps(data)), mimetype='application/json')

