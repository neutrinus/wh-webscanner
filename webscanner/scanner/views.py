# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.db import transaction
from urlparse import urlparse, urlunparse
from urllib import unquote_plus
from annoying.decorators import render_to
import json
import re
from logs import log
from scanner.models import *
from account.models import UserProfile
from django.views.decorators.cache import cache_page


def index(request):
	return render_to_response('scanner/index.html', {}, context_instance=RequestContext(request))

@render_to('terms.html')
def terms(request):
    return dict()

@render_to('about.html')
def about(request):
    return dict()

@render_to('pricing.html')
def pricing(request):
    return dict()

@login_required
@render_to('scanner/scan_archive.html')
def scan_archive(request):
    return dict(
        tests = Tests.objects.filter(user = request.user).order_by('-creation_date'),
    )


def results(request):
    """ page with scann results """
    if request.method == 'POST':
        url = request.POST.get("url").lower()


        #basic url validiation
        url = re.sub(r'\s+$', '', url)
        url = re.sub(r'^\s+', '', url)

        if not urlparse(url).scheme:
            url = "http://"+url
        if (urlparse(url).scheme not in ["http","https"]) or \
           (not urlparse(url).netloc) or \
           len(urlparse(url).netloc) < 3:
            messages.warning(request, _('Invalid website address (URL), please try again.'))
            return redirect(reverse('scanner_index'))
        url = unquote_plus(url)

        if not urlparse(url).path:
            url += "/"

        # loop over to run unparse
        urlk = urlparse(urlunparse(urlparse(url)))

        if request.user.is_authenticated():
            user_profile =  UserProfile.objects.get_or_create(user = request.user)[0]

        if request.user.is_authenticated() and user_profile.is_paid():
            url = urlk.geturl()
        else:
            if urlk.scheme == "http" and  ( urlk.port == 80 or urlk.port == None):
                url = urlk.scheme + '://' + urlk.netloc + urlk.path
            else:
                messages.warning(request, _('Only VIP members are allowed to use non-standart port or https!'))
                return redirect(reverse('scanner_index'))

            # non-VIP - check last scan.date for this url
            last_tests = Tests.objects.filter(url=url).order_by("-creation_date")
            if len(last_tests) >0:
                if last_tests[0].creation_date > dt.now() - td(days=1):
                    return render_to_response('scanner/scan_denied.html',
                                              {
                                                'last_test': last_tests[0],
                                                'url': url,
                                              },
                                              context_instance=RequestContext(request))

        if request.user.is_authenticated():
            if user_profile.is_paid():
                test = Tests(url=url, user=request.user, priority=40, vip_mode=True)
            else:
                test = Tests(url=url, user=request.user, priority=20)
        else:
            test = Tests(url=url)
        test.save()

        log.debug("User ordered report for url:%s, report_uuid:%s"%(url,test.uuid))

        # order all posible commands in transaction - huge performance gain
        with transaction.commit_on_success():
            for testname,plugin in TESTDEF_PLUGINS:
                oplugin = PLUGINS[ testname ]()
                a = CommandQueue(test=test, testname = testname, wait_for_download = oplugin.wait_for_download )
                a.save()
        #TODO: please dont hardcode urls..
        return redirect('/reports/'+ test.uuid)
    else:
        return redirect(reverse('scanner_index'))

def show_report(request, uuid):
    try:
        test = Tests.objects.filter(uuid=uuid).get()
    except ObjectDoesNotExist:
        messages.warning(request, _('Report not found, please check ID and URL'))
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

