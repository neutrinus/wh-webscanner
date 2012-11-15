# -*- encoding: utf-8 -*-

#django import
from django.db import models
from django.utils.translation import (ugettext as __,ugettext_lazy as _, get_language)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core import signing
from django_extensions.db.fields import UUIDField
from django.core.cache import cache
from django.db.models import Count
from django.db.models import Max
from django.conf import settings
from datetime import datetime
#3rd party import
from urlparse import urlparse
from model_utils import Choices
from datetime import datetime as dt, timedelta as td
#local imports
from logs import log

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
from scanner.plugins.optiimg import PluginOptiimg
from scanner.plugins.optiyui import PluginOptiYUI
from scanner.plugins.check_spelling import PluginCheckSpelling
from scanner.plugins.check_google_site import PluginGoogleSite
from scanner.plugins.social import PluginSocial


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
    ('optiimg', PluginOptiimg ),
    ('spellcheck', PluginCheckSpelling),
    ('optiyui', PluginOptiYUI),
    ('social', PluginSocial),
    #('googlesite', PluginGoogleSite ),
))

PLUGIN_NAMES = [ (code,plugin.name) for code,plugin in PLUGINS.items() ]

SHOW_LANGUAGES = [ item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES ]


class Tests(models.Model):
    TEST_STATUS = Choices(
        ('not_started', _("Not started")),
        ('started', _("Scheduled")),
        ('stopped', _("Stopped")),
    )
    TEST_GROUPS = {
        'seo': {'verbose_name':_('SEO checks'),
                'test_codes':('social','spellcheck')},
        'performance': {'verbose_name':_('SEO checks'),
                'test_codes':('social','spellcheck')},
        'security': {'verbose_name':_('SEO checks'),
                'test_codes':('social','spellcheck')},
        'mail': {'verbose_name': _("Mail checks"),
                'test_codes':('social',)},
    }
    '''
    Fields with _ prefix should not be used for queries, there are only
    some kind of `calculated cache`.
    '''
    uuid                =   UUIDField(db_index=True,auto=True, unique=True)
    url                 =   models.CharField(max_length=600,blank=1,null=1, db_index=True)
    priority            =   models.IntegerField(default=10)
    creation_date       =   models.DateTimeField(auto_now_add=True, db_index=True)

    download_status     =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    download_path       =   models.CharField(max_length=300,blank=1,null=1,db_index=True)

    user                =   models.ForeignKey(User, null=1)
    user_ip             =   models.IPAddressField(null=True)

    is_deleted          =   models.BooleanField(_(u'has been removed'), default=False)

    #: Cache for: status
    _status           =   models.CharField(_(u'status'),
                                           max_length=16,
                                           choices=TEST_STATUS,
                                           default=TEST_STATUS.not_started)

    #: Cache for `CommandQueue` duration
    _total_duration     =   models.PositiveIntegerField(blank=True, null=True)



    def __unicode__(self):
        return "%s by %s"%(self.url,self.user )

    @models.permalink
    def get_absolute_url(self):
        ''' link to results'''
        return 'scanner_report', (), {'uuid':self.uuid}

    def domain(self):
        return urlparse(self.url).hostname

    def port(self):
        if urlparse(self.url).port:
            return(urlparse(self.url).port)
        else:
            return(80)

    def percent_progress(self):
        '''
        Show in percentage, how much test's commands are active now.
        '''
        if self._status == self.TEST_STATUS.not_started: return 0.0
        if self._status == self.TEST_STATUS.stopped: return 100.0

        done = float(self.commands.not_active().count())
        total = float(self.commands.count())

        if total <= 0.1:
            return 0.0
        else:
            percent = (done/total) * 100.0
            return percent

    def duration(self):
        if self._status == self.TEST_STATUS.not_started: return 0
        elif self._status == self.TEST_STATUS.started:
            return (datetime.now() - self.creation_date).total_seconds()
        elif self._status == self.TEST_STATUS.stopped:
            #all test finished
            if not self._total_duration:
                # if there is no cache, fill it
                self._total_duration = (self.commands.last_finish_date()\
                                       - self.creation_date).total_seconds()
                self.save()
            return self._total_duration

        log.error('duration assertion: this error should never exist!')
        return 0

    def start(self, test_codes=None, test_groups=None):
        # TODO: make usable of `test_names` and `test_groups`
        if self._status in (self.TEST_STATUS.started, self.TEST_STATUS.stopped):
            return False

        # commands to schedule (command codes)
        codes = set(code for code in PLUGINS.keys())
        commands = set()

        if test_codes is None and test_groups is None:
            # if nothing selected, do all tests
            commands = codes
        else:
            if test_codes:
                test_codes = set(test_codes)
                if test_codes.difference(codes):
                    raise ValueError("You passed invalid test codes: %s"%
                        ', '.join(test_codes.difference(codes)))
                commands.update(test_codes)
            if test_groups:
                test_groups = set(test_groups)
                if test_groups.difference(self.TEST_GROUPS.keys()):
                    raise ValueError("You passed invalid test group codes: %s"%
                        ', '.join(test_groups.difference(self.TEST_GROUPS.keys())))
                for group_code in test_groups:
                    commands.update(self.TEST_GROUPS[group_code]['test_codes'])

        try:
            command_queue = []
            for code in commands:
                oplugin = PLUGINS[code]()
                command_queue.append(
                    CommandQueue(test=self,
                                 testname=code,
                                 wait_for_download=oplugin.wait_for_download)
                )

            with transaction.commit_on_success():
                self._status = self.TEST_STATUS.started
                self.save()
                [ cmd.save() for cmd in command_queue ]
            return True
        except Exception:
            log.exception("Error during starting test: %s"%self.uuid)
            raise


    @classmethod
    def unsign_url(cls, signed_url):
        '''
        Check signature of signed url and return
        url and groups (signed with :meth:`sign_url`)

        :param signed_url: signed url
        :type signed_url: str
        :returns: list with url and list of test group names (ex: url, (gr1, gr2))
        :rtype: list
        :raises: BadSignature (from django signing)
        '''
        item = signing.loads(signed_url)
        if not isinstance(item, list) and len(item) == 2:
            raise signing.BadSignature
        url, groups = item
        if not isinstance(url, basestring):
            raise signing.BadSignature
        if not isinstance(groups, list):
            raise signing.BadSignature
        return url, groups
        

    @classmethod
    def sign_url(cls, url, groups=None):
        '''
        Sign url with selected test groups and return as string
        with signature

        :param url: url
        :type url: str
        :param groups: tuple of strings from TEST_GROUP
        :type groups: tuple
        :returns: encoded string
        :rtype: str

        List can be tuples as well.
        '''
        if not isinstance(url, basestring):
            raise TypeError
        if not isinstance(groups, (tuple, list)):
            raise TypeError
        return signing.dumps((url, groups))

    @classmethod
    def create_from_signed_url(cls, signed_url, user, user_ip=None):
        '''
        Creates test and commands for signed_url url and groups
        '''
        if signed_url is None:
            return None
        url, groups = cls.unsign_url(signed_url)
        ctx = dict(
            url=url,
            user=user,
        )
        if user_ip:
            ctx['user_ip']=user_ip

        test = Tests.objects.create(**ctx)
        test.start(test_groups=groups)
        return test

class CommandQueueManager(models.Manager):
    def last_finish_date(self):
        return self.get_query_set()\
            .aggregate(Max('finish_date'))['finish_date__max']

    def active(self):
        return self.get_query_set()\
            .filter(status__in=[STATUS.waiting, STATUS.running])

    def not_active(self):
        return self.get_query_set()\
            .filter(status__in=[STATUS.success, STATUS.unsuccess,
                    STATUS.exception])


class CommandQueue(models.Model):

    test                =   models.ForeignKey(Tests, related_name="commands")
    status              =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    testname            =   models.CharField(max_length=50, choices=PLUGIN_NAMES)

    run_date            =   models.DateTimeField(default=None,blank=1,null=1)
    finish_date         =   models.DateTimeField(default=None,blank=1,null=1)
    wait_for_download   =   models.BooleanField(default=True, db_index=True)

    objects = CommandQueueManager()

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
        return "%s: %s(%s)"%(self.test.domain(),self.output_desc,unicode(dict(RESULT_STATUS)[self.status]))


#: Model for check_spell plugin to keep 'bad' words (bad, but we want to keep
#: them ;])
class BadWord(models.Model):
    word = models.CharField(max_length=128, db_index=True)
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
            #log.debug(' * %s '%bad_words)
        else:
            log.debug('Bad words loaded from cache (%d)'%len(bad_words))
            #log.debug(' * %s'%bad_words)

        ok_words = list(( w for w in words if w.strip().lower() not in bad_words ))

        return ok_words
