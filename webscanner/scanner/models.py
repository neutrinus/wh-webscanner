# -*- encoding: utf-8 -*-

#django import
from django.db import models
from django.utils.translation import (ugettext as __,ugettext_lazy as _, get_language)
from django.contrib.auth.models import User 
from django.core.exceptions import ValidationError
from django.conf import settings

#3rd party import
from model_utils import Choices
from datetime import datetime as dt, timedelta as td
from logging import getLogger
log = getLogger('scanner.models')

#local imports

STATUS = Choices(
    (-3, 'waiting',  _(u'wait for processing')),
    (-2, 'running',  _(u'in progress')),
    (-1, 'unsuccess',_(u'unsuccess')),
    (0,  'success',  _(u'success')),
    (1,  'exception',_(u'exception')),
    (2,  'other',    _(u'Unknown')),
)

RESULT_STATUS = Choices(
    (0,  'success',  _(u'Success')),
    (1,  'error',_(u'Error')),
    (2,  'warning',    _(u'Warning')),
    (3,  'info',    _(u'info'))
)

RESULT_GROUP = Choices(
    (0,  'general',_(u'General')),
    (1,  'mail',  _(u'E-mail related')),
    (2,  'seo',    _(u'SEO')),
    (3,  'security',    _(u'Security')),
    (4,  'screenshot',    _(u'Screenshot'))
)


from scanner.plugins.check_http_code import PluginCheckHTTPCode
from scanner.plugins.check_w3c_valid import PluginCheckW3CValid
from scanner.plugins.check_googlesb import PluginGoogleSafeBrowsing
from scanner.plugins.check_domainexpdate import PluginDomainExpireDate
from scanner.plugins.check_clamav import PluginClamav
from scanner.plugins.check_dns_mail import PluginDNSmail
from scanner.plugins.check_dns import PluginDNS
from scanner.plugins.check_dns_mail_rbl import PluginDNSmailRBL
from scanner.plugins.check_pagerank import PluginPagerank
from scanner.plugins.check_mail import PluginMail
from scanner.plugins.screenshot_firefox import PluginMakeScreenshotFirefox



PLUGINS = dict((
    ('http_code', PluginCheckHTTPCode ),
    ('w3c_valid', PluginCheckW3CValid ),
    ('googlesb', PluginGoogleSafeBrowsing ),
    ('domainexpdate', PluginDomainExpireDate ),
    ('clamav', PluginClamav ),
    ('dns', PluginDNS ),
    ('dns_mail', PluginDNSmail ),
    ('dns_mail_rbl', PluginDNSmailRBL ),
    ('pagerank', PluginPagerank ),
    ('mail', PluginMail ),
    ('screenshot_ff', PluginMakeScreenshotFirefox ),
))

TESTDEF_PLUGINS = [ (code,plugin.name) for code,plugin in PLUGINS.items() ]

SHOW_LANGUAGES = [ item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES ]
        
        
class Tests(models.Model):
    domain              =   models.CharField(max_length=300,blank=1,null=1,db_index=True)
    priority            =   models.IntegerField(default=10)
#   lang?    
    creation_date       =   models.DateTimeField(auto_now_add=True)
    
    download_status     =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    download_path       =   models.CharField(max_length=300,blank=1,null=1,db_index=True)
    
    def __unicode__(self):
        return "%s"%(self.domain)


class CommandQueue(models.Model):
    test                =   models.ForeignKey(Tests, related_name="command for test")    
    status              =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    testname            =   models.CharField(max_length=50, choices=TESTDEF_PLUGINS)
    
    run_date            =   models.DateTimeField(default=None,blank=1,null=1)
    finish_date         =   models.DateTimeField(default=None,blank=1,null=1)   
    wait_for_download   =   models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s: status=%s"%(self.test.domain,unicode(dict(STATUS)[self.status]))


        
class Results(models.Model):
    test                =   models.ForeignKey(Tests, related_name="results for test")    
    
    status              =   models.IntegerField(choices=RESULT_STATUS)
    group               =   models.IntegerField(choices=RESULT_GROUP)
    output_desc         =   models.CharField(max_length=10000)  
    output_full         =   models.CharField(max_length=10000)  

    # used to calculate overal note rank in results (1-5))
    importance          =   models.IntegerField(default=2)
    
    creation_date       =   models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s: name=%s(%s)"%(self.test.domain,self.output_desc,unicode(dict(RESULT_STATUS)[self.status]))

