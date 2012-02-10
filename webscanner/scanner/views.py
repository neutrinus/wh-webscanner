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
from django.http import HttpResponse
from urlparse import urlparse
from annoying.decorators import render_to
from scanner.models import *
from logs import log


def index(request):
	#recipe_list = Recipe.objects.filter(is_deleted=False).order_by('-created_at')

	return render_to_response('index.html', {}, context_instance=RequestContext(request))



def results(request):
    
    if request.method == 'POST':
        url = request.POST.get("url")
        log.debug("User requested tests for url:%s"%(url))
        
        if not urlparse(url).scheme:
            url = "http://"+url
        
        if urlparse(url).scheme not in ["http","https"]:
            return redirect('/')    
        
        test = Tests(url=url)
        test.save()
        request.session['testid'] = test.pk;
            
        for testname,plugin in TESTDEF_PLUGINS:
            oplugin = PLUGINS[ testname ]()    
            a = CommandQueue(test=test, testname = testname, wait_for_download = oplugin.wait_for_download )
            a.save()
    
        return render_to_response('results.html', {'test': test}, context_instance=RequestContext(request))        
    else:
        return redirect('/')
        
    
    #recipe_list = Recipe.objects.filter(is_deleted=False).order_by('-created_at')
    
    

def scan_progress(request):
    testid = request.session.get('testid', False)
    
    test = Tests(pk=testid)
    
    commands_count = CommandQueue.objects.filter(test=test).count()
    commands_done_count = CommandQueue.objects.filter(test=test).exclude(status=STATUS.waiting).exclude(status=STATUS.running).count()
        
    #print req.GET, req.POST
    data = {'testid':testid, 'ordered': commands_count, "done": commands_done_count}
    return HttpResponse('%s(%s)'%(request.GET.get('callback',''),  json.dumps(data)), mimetype='application/json')
        
    
    
def check_results(request,last_date=None):
    testid = request.session.get('testid', False)
    test = Tests(pk=testid)

    lastresult = request.session.get('lastresult', False)
    if not lastresult:
        lastresult = 0;
    
    results = Results.objects.filter(test=test).filter(pk__gt = lastresult)
    
    foo = []
    for result in results:
        foo.append({'output_desc':result.output_desc,
                    'output_full':result.output_full,
                    'status': result.status,
                    'importance': result.importance,
                    'group': result.group})
        if result.pk > lastresult:
            lastresult = result.pk
    
    request.session['lastresult'] = lastresult;
    return HttpResponse('%s(%s)'%(request.GET.get('callback',''),  json.dumps(foo)), mimetype='application/json')
    
    
    
    

