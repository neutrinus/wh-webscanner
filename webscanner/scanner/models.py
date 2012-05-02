# -*- encoding: utf-8 -*-

#django import
from django.db import models
from django.utils.translation import (ugettext as __,ugettext_lazy as _, get_language)
from django.contrib.auth.models import User 
from django.core.exceptions import ValidationError
from django_extensions.db.fields import UUIDField
from django.core.cache import cache
from django.db.models import Count

from django.conf import settings

#3rd party import
from urlparse import urlparse
from model_utils import Choices
from datetime import datetime as dt, timedelta as td
from logs import log
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
    (4,  'screenshot',    _(u'Screenshot')),
    (5,  'performance',    _(u'Performance')),
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
from scanner.plugins.screenshots import PluginMakeScreenshots
from scanner.plugins.check_surbl import PluginSURBL
from scanner.plugins.check_plainemail import PluginPlainTextEmail
from scanner.plugins.check_robots import PluginCheckRobots
from scanner.plugins.check_optipng import PluginOptipng
from scanner.plugins.check_spelling import PluginCheckSpelling
from scanner.plugins.check_google_site import PluginGoogleSite



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
    ('screenshots', PluginMakeScreenshots ),
    ('surbl', PluginSURBL ),
    ('robots', PluginCheckRobots ),
    ('plainemail', PluginPlainTextEmail ),
    ('optipng', PluginOptipng ),
    ('spellcheck', PluginCheckSpelling),
    ('googlesite', PluginGoogleSite ),
))

TESTDEF_PLUGINS = [ (code,plugin.name) for code,plugin in PLUGINS.items() ]

SHOW_LANGUAGES = [ item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES ]
        
        
class Tests(models.Model):
    url                 =   models.CharField(max_length=600,blank=1,null=1,db_index=True)
    priority            =   models.IntegerField(default=10)
#   lang?    
    creation_date       =   models.DateTimeField(auto_now_add=True)
    
    download_status     =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    download_path       =   models.CharField(max_length=300,blank=1,null=1,db_index=True)
    uuid                =   UUIDField()
    
    def __unicode__(self):
        return "%s"%(self.url)
        
    def domain(self):
        return urlparse(self.url).hostname
        
    def port(self):
        if urlparse(self.url).port:
            return(urlparse(self.url).port)
        else:
            return(80)
            

class CommandQueue(models.Model):
    test                =   models.ForeignKey(Tests, related_name="commands")    
    status              =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    testname            =   models.CharField(max_length=50, choices=TESTDEF_PLUGINS)
    
    run_date            =   models.DateTimeField(default=None,blank=1,null=1)
    finish_date         =   models.DateTimeField(default=None,blank=1,null=1)   
    wait_for_download   =   models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s: status=%s"%(self.test.domain(),unicode(dict(STATUS)[self.status]))


class Results(models.Model):
    test                =   models.ForeignKey(Tests, related_name="result")
    
    status              =   models.IntegerField(choices=RESULT_STATUS)
    group               =   models.IntegerField(choices=RESULT_GROUP)
    output_desc         =   models.CharField(max_length=10000)  
    output_full         =   models.TextField()  

    # used to calculate overal note rank in results (1-5))
    importance          =   models.IntegerField(default=2)
    
    creation_date       =   models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s: name=%s(%s)"%(self.test.domain(),self.output_desc,unicode(dict(RESULT_STATUS)[self.status]))


#: Model for check_spell plugin to keep 'bad' words (bad, but we want to keep
#: them ;])
class BadWord(models.Model):
    word = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.word

    def __repr__(self):
        return u'<%s: %s (seen:%s)'%(self.__class__.__name__,
                                     self.word,
                                     self.timestamp)

    def save(self,*a,**b):
        self.word = self.word.strip().lower()
        super(BadWord, self).save(*a,**b)

    @staticmethod
    def clean_bad_words(date=None):
        'default date is 30 days'
        if date is None:
            date = dt.now() - td(days=30)
        elif isinstance(date, int):
            date = dt.now() - td(days=date)
        log.info('Cleaning "bad words" older than: %s.' % date)

        bad_words = BadWord.objects.filter(timestamp__lt=date).count()
        log.info('Deleted "bad words": %d.' % bad_words)
        bad_words = BadWord.objects.filter(timestamp__lt=date).delete()
        return bad_words

    @staticmethod
    def filter_bad_words(words):
        bad_words = cache.get('scanner.bad_words') 

        # do caching if not in cache
        BadWord.clean_bad_words()

        if not bad_words:

            # when saving to cache, clear DB :)

            bad_words = BadWord.objects.values('word').order_by().\
                    annotate(count=Count('word'))

            bad_words = set((
                w['word'] for w in bad_words if w['count'] > \
                    PluginCheckSpelling.bad_word_limit
            ))

            cache.set('scanner.bad_words', bad_words, 60*60*24)

            log.debug('Bad words saved to cache (%d bad words)'%len(bad_words))
            log.debug(' * %s '%bad_words)
        else:
            log.debug('Bad words loaded from cache')
            log.debug(' * %s'%bad_words)

        ok_words = list(( w for w in words if w.strip().lower() not in bad_words ))

        return ok_words
