# -*- encoding: utf-8 -*-

import logging
#django import
from django.db import models
from django.utils.translation import ugettext_lazy as _
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

log = logging.getLogger(__name__)

STATUS = Choices(
    (-3, 'waiting',   _(u'wait for processing')),
    (-2, 'running',   _(u'in progress')),
    (-1, 'unsuccess', _(u'unsuccess')),
    (0,  'success',   _(u'success')),
    (1,  'exception', _(u'exception')),
    (2,  'other',     _(u'Unknown')),
)

RESULT_STATUS = Choices(
    (0,  'success',  _(u'Success')),
    (1,  'error',    _(u'Error')),
    (2,  'warning',  _(u'Warning')),
    (3,  'info',     _(u'info'))
)

RESULT_GROUP = Choices(
    (0,  'general',     _(u'General')),
    (1,  'mail',        _(u'E-mail related')),
    (2,  'seo',         _(u'SEO')),
    (3,  'security',    _(u'Security')),
    (4,  'screenshot',  _(u'Screenshot')),
    (5,  'performance', _(u'Performance')),
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
from scanner.plugins.check_surbl import PluginSURBL
from scanner.plugins.check_plainemail import PluginPlainTextEmail
from scanner.plugins.check_robots import PluginCheckRobots
from scanner.plugins.optiimg import PluginOptiimg
from scanner.plugins.screenshots import PluginMakeScreenshots
from scanner.plugins.optiyui import PluginOptiYUI
from scanner.plugins.check_spelling import PluginCheckSpelling
#from scanner.plugins.check_google_site import PluginGoogleSite
from scanner.plugins.social import PluginSocial


PLUGINS = dict((
    ('http_code', PluginCheckHTTPCode),
    ('w3c_valid', PluginCheckW3CValid),
    ('googlesb', PluginGoogleSafeBrowsing),
    ('domainexpdate', PluginDomainExpireDate),
    ('clamav', PluginClamav),
    ('dns', PluginDNS),
    ('dns_mail', PluginDNSmail),
    ('dns_mail_rbl', PluginDNSmailRBL),
    ('pagerank', PluginPagerank),
    ('mail', PluginMail),
    ('screenshots', PluginMakeScreenshots),
    ('surbl', PluginSURBL),
    ('robots', PluginCheckRobots),
    ('plainemail', PluginPlainTextEmail),
    ('optiimg', PluginOptiimg),
    ('spellcheck', PluginCheckSpelling),
    ('optiyui', PluginOptiYUI),
    ('social', PluginSocial),
    #('googlesite', PluginGoogleSite ),
))


PLUGIN_NAMES = [(code, plugin.name) for code, plugin in PLUGINS.items()]


SHOW_LANGUAGES = [item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES]


def validate_groups(groups):
    'create validator that checks item is string of comma semarated group codes'
    def validator(value):
        item_groups = set(i for i in value.split(',') if i.strip())
        diff = item_groups.difference(set(groups))
        if diff:
            raise ValidationError(_('You selected groups "%s" which are not '
                                    'recognized by the system.' % ', '.join(diff)))
    return validator


class Tests(models.Model):
    class StartError(Exception):
        pass

    class AlreadyStartedError(StartError):
        pass

    TEST_STATUS = Choices(
        ('not_started', _("Not started")),
        ('started', _("Scheduled")),
        ('stopped', _("Stopped")),
    )

    '''
    Fields with _ prefix should not be used for queries, there are only
    some kind of `calculated cache`.
    '''

    ####
    # Attributes set during scan creation
    ####
    uuid                =   UUIDField(db_index=True, auto=True, unique=True)
    url                 =   models.CharField(max_length=600, blank=1, null=1, db_index=True)
    priority            =   models.IntegerField(default=10)
    creation_date       =   models.DateTimeField(auto_now_add=True, db_index=True)
    #: comma separated group codes from TEST_GROUPS
    check_security      =   models.BooleanField(default=True)
    check_seo           =   models.BooleanField(default=True)
    check_performance   =   models.BooleanField(default=True)
    check_mail          =   models.BooleanField(default=True)

    user                =   models.ForeignKey(User, null=1)
    user_ip             =   models.IPAddressField(null=True)

    ####
    # Attributes that can be changed during checks
    ####

    download_status     =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    download_path       =   models.CharField(max_length=300,blank=1,null=1,db_index=True)

    is_deleted          =   models.BooleanField(_(u'has been removed'), default=False)

    ####
    # Attributes which should be only changed by model instance itself
    ####

    #: Cache for: status
    _status           =   models.CharField(_(u'status'),
                                           max_length=16,
                                           choices=TEST_STATUS,
                                           default=TEST_STATUS.not_started)

    #: Cache for `CommandQueue` duration
    _total_duration     =   models.PositiveIntegerField(blank=True, null=True)



    def __unicode__(self):
        return "%s by %s" % (self.url,self.user)

    def __repr__(self):
        return '<Test uuid:%s url:%s user:%r>'%(self.uuid, self.url, self.user)

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
        '''
        Warning: this method call `save`
        '''
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

    @property
    def cost(self):
        '''
        This method calculate cost of a test (in credits)
        TODO: make it cachable as db field
        '''
        return 1

    def start(self, check_user_credits=True):
        '''
        Warning: this method call `save` for `self` and `self.user.userprofile`
        This method creates Commands for this tests.

        if `check_user_credits` is True and user is not None this method
        check user has enough credits level to start this task (use `cost` to
        calculate test cost). If user has not enough credits, NotEnoughCredits
        exception is raised. If user has enough credits, the cost is subtracted
        from his account and profile is saved!
        '''
        # if test is not saved
        if not self.pk:
            raise self.StartError('Test %r is not saved'%self)
        if self._status in (self.TEST_STATUS.started, self.TEST_STATUS.stopped):
            raise self.AlreadyStartedError('Test %r is already started'%self)

        log.debug('%r.start'%self)

        # check user has enough credits level to start this
        if check_user_credits and self.user:
            log.debug('%r.checking credits for user %r'%(self, self.user))
            if self.user.userprofile.credits < self.cost:
                raise self.user.userprofile.NotEnoughCredits(self.user.userprofile.credits,
                                                             self.cost,
                                                             _('start a scan'))
        log.info('%r.all checks done. starting commands'%self)

        try:
            with transaction.commit_on_success():
                for plugin_code, plugin_class in PLUGINS.items():
                    CommandQueue.objects.create(test=self,
                         testname=plugin_code,
                         wait_for_download=plugin_class.wait_for_download)
                self._status = self.TEST_STATUS.started

                # pay for test
                if self.user:
                    log.debug('%r just paid %s credits for test %r'%(
                        self.user, self.cost, self))
                    profile = self.user.userprofile
                    from django.db.models import F
                    profile.credits = F('credits') - self.cost
                    profile.save()

                self.save()
            log.info('%r.test started. commands started.'%self)
            return True
        except Exception as error:
            log.exception("Error during starting test: %r"%self)
            raise self.StartError(error)


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
    def make_from_signed_url(cls, signed_url, user, user_ip=None, **kwargs):
        '''
        Makes test and commands for signed_url url and groups (without saving it)

        :param kwargs: override Test attributes
        '''
        url, groups = cls.unsign_url(signed_url)
        ctx = dict(
            url=url,
            user=user,
        )
        # hardcoded test groups, it will be changed in next architecture redesign
        for key in ['check_seo','check_performance','check_mail','check_security']:
            ctx[key]=True if key in groups else False

        if user_ip:
            ctx['user_ip']=user_ip

        ctx.update(kwargs)

        return Tests(**ctx)


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
