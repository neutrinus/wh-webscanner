# -*- coding: utf-8 -*-

import re
import json
import logging
from urllib import unquote_plus
from urlparse import urlparse, urlunparse
from datetime import datetime as dt, timedelta as td

from django import forms
from django.db.models import F
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.contrib import messages

import furl
from annoying.decorators import render_to

from scanner.models import *
from scanner.forms import FormCaptcha
from webscanner.apps.addonsapp.tools import extract_domain

log = logging.getLogger(__name__)


@render_to('terms.html')
def terms(request):
    return dict()

@render_to('about.html')
def about(request):
    return dict()

@login_required
@render_to('scanner/scan_archive.html')
def scan_archive(request):
    return dict(
        tests = request.user.tests_set.order_by('-creation_date'),
        #tests = Tests.objects.filter(user = request.user).order_by('-creation_date'),
    )


class ScanURLForm(forms.ModelForm):
    class Meta:
        model = Tests
        fields = 'url', 'check_seo', 'check_security', 'check_performance', 'check_mail'

    def clean_url(self):
        url = self.cleaned_data['url']

        #basic url validiation and normalization
        url = re.sub(r'\s+$', '', url)
        url = re.sub(r'^\s+', '', url)

        if not urlparse(url).scheme:
            url = "http://"+url
        if (urlparse(url).scheme not in ["http","https"]) or \
           (not urlparse(url).netloc) or \
           len(urlparse(url).netloc) < 3:
               raise forms.ValidationError(_('Invalid website address (URL), please try again.'))

        try:
            extract_domain(url)
        except ValueError:
            log.info('User passed "%s" as domain to scan -> ValidationError' % url)
            raise forms.ValidationError(_('Invalid website address (URL), please try again.'))

        url = unquote_plus(url)
        if not urlparse(url).path:
            url += "/"

        # loop over to run unparse
        urlk = urlparse(urlunparse(urlparse(url)))

        return urlk.geturl()

    def clean(self):
        log.debug('clean form')
        if (not self.cleaned_data['check_seo'] and
            not self.cleaned_data['check_performance'] and
            not self.cleaned_data['check_mail'] and
            not self.cleaned_data['check_security']):
            raise forms.ValidationError(_("Please, choose some tests."))
        return self.cleaned_data


@render_to('scanner/index.html')
def index(request):
    # check url is fine
    form = ScanURLForm(request.POST or None)
    if not request.POST:
        return {}

    if not form.is_valid():
        return {'form':form}

    # check captcha if we need it
    captcha_form = FormCaptcha(request.POST or None)
    if not captcha_form.is_valid():
        # captcha in most cases will not be valid.
        # When user scan a lot of sites (condition below) then we render
        # captcha to him and check this condition
        if Tests.objects.filter(user_ip=request.META['REMOTE_ADDR'],
            creation_date__gt=dt.now()-td(hours=1))\
            .count() > getattr(settings, 'WEBCHECK_CAPTCHA_SCANS_LIMIT', 30):

            log.warning("Limit per ip %s reached" % request.META['REMOTE_ADDR'])

            return {'TEMPLATE': 'scanner/scan_captcha.html',
                    'url': url,
                    'recaptcha_form':captcha}

    def get_test_group_codes():
        return filter(lambda x:x.startswith('check_'), request.POST)

    # if user is not authenticated, do inline registration
    if not request.user.is_authenticated():
        pass_url = Tests.sign_url(form.cleaned_data['url'], get_test_group_codes())
        redirect_url = furl.furl(reverse('registration_register_or_login_inline'))
        redirect_url.args['u']=pass_url
        return redirect(redirect_url.url)

    log.debug('preparing test from form (main page)')

    test = form.save(commit=False)
    test.user = request.user
    test.user_ip = request.META['REMOTE_ADDR']
    test.save()
    test.start()

    log.debug('redirecting to results')
    return redirect(reverse('scanner_report', kwargs={'uuid':test.uuid}))


def results(request):
    """ page with scann results """
    pass


@render_to('scanner/results.html')
def show_report(request, uuid):
    try:
        test = Tests.objects.filter(uuid=uuid).get()
        results = Results.objects.filter(test=test).order_by('-status')
        if results:
            last_pk = max(results, key=lambda x: x.pk).pk
        else:
            last_pk = 0
    except ObjectDoesNotExist:
        messages.warning(request, _('Report not found, please check ID and URL'))
        return redirect('/')
    return {'test': test,
            'results': results,
            'last_pk': last_pk,
            'stats_success': results.filter(status=RESULT_STATUS.success).count(),
            'stats_error': results.filter(status=RESULT_STATUS.error).count(),
            'stats_warning': results.filter(status=RESULT_STATUS.warning).count(),
            'stats_info': results.filter(status=RESULT_STATUS.info).count(),
    }


def check_results(request, uuid):
    """
    ajax requests handler - suply information about tests
    """
    if not request.is_ajax() and not settings.DEBUG:
        raise Exception("ERROR")
    if not request.GET.get('callback', None):
        raise Exception("ERROR")

    try:
        test = Tests.objects.get(uuid=uuid)
    except Tests.DoesNotExist:
        raise Http404

    last = request.GET.get("last")
    if not last:
        last = 0

    #results = Results.objects.filter(test=test).filter(pk__gt=last)
    results = test.results.filter(pk__gt=last).values('id',
                                                      'group',
                                                      'importance',
                                                      'status',
                                                      'output_desc',
                                                      'output_full')
    data = {'ordered': test.commands.count() + 1,
            "done": test.commands.not_active().count() + 1,
            "test_duration": test.duration(),
            "rating": test.calculate_rating(),
            "results": list(results)}

    return HttpResponse('%s(%s)' % (request.GET.get('callback', ''), json.dumps(data)), mimetype='application/json')


