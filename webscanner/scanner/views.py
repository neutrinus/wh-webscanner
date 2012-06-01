# -*- coding: utf-8 -*-
import json
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.views.generic.list_detail import object_list
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.contrib.comments.models import Comment
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.sitemaps import ping_google
from django.contrib.auth import logout
from django.http import HttpResponse
from urlparse import urlparse
from datetime import datetime
from annoying.decorators import render_to
from scanner.models import *
from logs import log
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.contrib import messages

def index(request):
	return render_to_response('index.html', {}, context_instance=RequestContext(request))

def results(request):
    if request.method == 'POST':
        url = request.POST.get("url")
        
        #basic url validiation
        if not urlparse(url).scheme:
            url = "http://"+url        
        if urlparse(url).scheme not in ["http","https"]:
            return redirect('/')    
        
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
        return redirect('/')

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
        
    return render_to_response('results.html', {'test': test}, context_instance=RequestContext(request))        

    
def check_results(request, uuid):
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
    
    commands_count = CommandQueue.objects.filter(test=test).count()
    commands_done_count = CommandQueue.objects.filter(test=test).exclude(status=STATUS.waiting).exclude(status=STATUS.running).count()

    if commands_count == commands_done_count: 
        #all test finished
        last_command = CommandQueue.objects.filter(test=test).aggregate(Max('finish_date'))['finish_date__max']
    else:
        last_command = datetime.now()
     
    test_duration = (last_command - test.creation_date).total_seconds()
    
    data = {    'ordered': commands_count+1,
                "done": commands_done_count+1,
                "test_duration": test_duration,
                "results": foo,
    }
        
    return HttpResponse('%s(%s)'%(request.GET.get('callback',''),  json.dumps(data)), mimetype='application/json')
    
   

def ulogout(request):
    logout(request)
    messages.success(request, _('You have ben logged-out. We will miss you!'))
    # Redirect to a success page.    
    return redirect('/')