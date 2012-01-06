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
    (-3, 'waiting',  _(u'Waiting for process')),
    (-2, 'running',  _(u'In progress')),
    (-1, 'unsuccess',_(u'Problem')),
    (0,  'success',  _(u'Success')),
    (1,  'exception',_(u'Error')),
    (2,  'other',    _(u'Unknown')),
)


from scanner.plugins.check_http_code import PluginCheckHTTPCode
#from gworker.plugins.check_w3c_valid import PluginCheckW3CValid
#from gworker.plugins.check_domainexpdate import PluginDomainExpireDate
#from gworker.plugins.check_kaspersky import PluginKaspersky

PLUGINS = dict((
    #('http_code', PluginCheckHTTPCode ),
    #('w3c_valid', PluginCheckW3CValid ),
    #('domainexpdate', PluginDomainExpireDate ),
    #('kaspersky', PluginKaspersky ),
))

TESTDEF_PLUGINS = [ (code,plugin.name) for code,plugin in PLUGINS.items() ]

SHOW_LANGUAGES = [ item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES ]
        

class TestQueue(models.Model):
    domain              =   models.CharField(max_length=300,blank=1,null=1,db_index=True)
    priority            =   models.IntegerField(default=10)
#   lang?    

    status              =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    testname            =   models.CharField(_(u'testdef'),    max_length=50,    choices=TESTDEF_PLUGINS,db_index=True)
    output              =   models.CharField(max_length=1000,blank=1,null=1)  
    
    creation_date       =   models.DateTimeField(auto_now_add=True)
    run_date            =   models.DateTimeField(auto_now=True)
    finish_date         =   models.DateTimeField(default=None,blank=1,null=1)
    
    def __unicode__(self):
        return "%s: status=%s:"%(self.domain,self.status)
        
