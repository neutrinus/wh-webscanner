# -*- encoding: utf-8 -*-

import os
import shutil
import logging
import math
from datetime import datetime

#django import
from django.db import models
from django.core import signing
from django.conf import settings
from django.db.models import Max
from django.db.models import Count
from django.db import transaction
from django.core import cache
from django.db.models.signals import pre_delete
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import UUIDField

from django.contrib.auth.models import User

#3rd party import
from urlparse import urlparse
from model_utils import Choices
from datetime import datetime as dt, timedelta as td

#local imports
from webscanner.utils.httrack import parse_new_txt
from webscanner.utils.http import extract_domain_from_url, extract_root_domain

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


from .plugins.check_http_code import PluginCheckHTTPCode
from .plugins.check_w3c_valid import PluginCheckW3CValid
from .plugins.check_googlesb import PluginGoogleSafeBrowsing
from .plugins.check_domainexpdate import PluginDomainExpireDate
from .plugins.check_clamav import PluginClamav
from .plugins.check_dns_mail import PluginDNSmail
from .plugins.check_dns import PluginDNS
from .plugins.check_dns_mail_rbl import PluginDNSmailRBL
from .plugins.check_pagerank import PluginPagerank
from .plugins.check_mail import PluginMail
from .plugins.check_surbl import PluginSURBL
from .plugins.check_plainemail import PluginPlainTextEmail
from .plugins.check_robots import PluginCheckRobots
from .plugins.optiimg import PluginOptiimg
from .plugins.screenshots import PluginMakeScreenshots
from .plugins.optiyui import PluginOptiYUI
from .plugins.check_spelling import PluginCheckSpelling
#from scanner.plugins.check_google_site import PluginGoogleSite
from .plugins.social import PluginSocial
from .plugins.check_urllength import PluginUrlLength
from .plugins.check_seotags import PluginSEOTags
from .plugins.check_html2text_ratio import PluginHtml2TextRatio
from .plugins.check_requests import PluginRequests


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
    ('urllength', PluginUrlLength),
    ('seo_tags', PluginSEOTags),
    ('html2text ratio', PluginHtml2TextRatio),
    ('requests', PluginRequests),
))


PLUGIN_NAMES = [(code, plugin.name) for code, plugin in PLUGINS.items()]


SHOW_LANGUAGES = [item for item in settings.LANGUAGES if item[0] in
                  settings.SHOW_LANGUAGES]


gcache = cache.get_cache('default')
lcache = cache.get_cache('local')


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
    class Meta:
        verbose_name = 'test'
        verbose_name_plural = 'tests'
    WEBSCANNER_TEST_PUBLIC_DATA_PATH = getattr(settings, 'WEBSCANNER_TEST_PUBLIC_DATA_PATH')
    WEBSCANNER_TEST_PUBLIC_DATA_URL = getattr(settings, 'WEBSCANNER_TEST_PUBLIC_DATA_URL')
    WEBSCANNER_TEST_PRIVATE_DATA_PATH = getattr(settings, 'WEBSCANNER_TEST_PRIVATE_DATA_PATH')

    class StartError(Exception):
        pass

    class AlreadyStartedError(StartError):
        pass

    ####
    # Attributes set during scan creation
    ####
    uuid                =   UUIDField(db_index=True, auto=True, unique=True)
    url                 =   models.CharField(max_length=600, blank=1, null=1, db_index=True)
    creation_date       =   models.DateTimeField(auto_now_add=True, db_index=True)
    #: comma separated group codes from TEST_GROUPS
    check_security      =   models.BooleanField(default=True)
    check_seo           =   models.BooleanField(default=True)
    check_performance   =   models.BooleanField(default=True)
    check_mail          =   models.BooleanField(default=True)

    user                =   models.ForeignKey(User, null=1, db_index=True)
    user_ip             =   models.IPAddressField(null=True, db_index=True)

    ####
    # Attributes that can be changed during checks
    ####

    download_run_date   =   models.DateTimeField(blank=True, null=True, default=None)
    download_status     =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    download_path       =   models.CharField(max_length=300, blank=1, null=1, db_index=True)

    is_deleted          =   models.BooleanField(_(u'has been removed'), default=False, db_index=True)

    def __unicode__(self):
        return u"%s by %s" % (self.url, self.user)

    def __repr__(self):
        return '<Test uuid:{} url:{} user:{!r}>'.format(self.uuid,
                                                        self.url.encode('utf-8', 'backslashreplace'),
                                                        self.user)

    @models.permalink
    def get_absolute_url(self):
        ''' link to results'''
        return 'scanner_report', (), {'uuid': self.uuid}

    def domain(self):
        return self.domain_name().encode('idna')

    def domain_name(self):
        return extract_domain_from_url(self.url)

    def root_domain(self):
        self.root_domain_name().encode('idna')

    def root_domain_name(self):
        return extract_root_domain(self.domain())

    def port(self):
        if urlparse(self.url).port:
            return(urlparse(self.url).port)
        else:
            return(80)

    def percent_progress(self):
        '''
        Show in percentage, how much test's commands are active now.
        '''
        done = float(self.commands.not_active().count())
        total = float(self.commands.count())
        if total <= 0.1:
            return 0.0
        else:
            percent = (done / total) * 100.0
            if percent >= 100.0:
                return 100.0
            return percent

    def is_done(self):
        if self.percent_progress() == 100.0:
            return True
        return False

    def duration(self):
        '''
        returns duration of a test in seconds
        '''
        if not self.is_done():
            return (datetime.utcnow() - self.creation_date).total_seconds()
        else:
            last = self.commands.last_finish_date()
            if not last:
                last = dt.utcnow()
            return (last - self.creation_date). total_seconds()

    @property
    def cost(self):
        '''
        This method calculate cost of a test (in credits)
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
        if self.commands.all().count() > 0:
            raise self.AlreadyStartedError('Test %r is already started'%self)

        log.debug('%r.start'%self)

        # check user has enough credits level to start this
        if check_user_credits and self.user:
            log.debug('%r.checking credits for user %r'%(self, self.user))
            if self.user.userprofile.credits < self.cost:
                self.delete()
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

                # pay for test
                if self.user:
                    profile = self.user.userprofile
                    from django.db.models import F
                    profile.credits = F('credits') - self.cost
                    profile.save()
                    log.info('%r just paid %s credits for test %r' % (
                        self.user, self.cost, self))
                if not os.path.exists(self.public_data_path):
                    os.makedirs(self.public_data_path)
                if not os.path.exists(self.private_data_path):
                    os.makedirs(self.private_data_path)
                self.save()
            log.info('%r.test started. commands started.' % self)
            return True
        except Exception as error:
            log.exception("Error during starting test: %r" % self)
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
        for key in ['check_seo', 'check_performance', 'check_mail', 'check_security']:
            ctx[key] = True if key in groups else False

        if user_ip:
            ctx['user_ip'] = user_ip

        ctx.update(kwargs)

        return Tests(**ctx)

    @property
    def public_data_path(self):
        if not self.uuid or not self.pk:
            raise self.DoesNotExist('%r is not saved. cannot calculate public_data_path' % self)
        return os.path.join(self.WEBSCANNER_TEST_PUBLIC_DATA_PATH,
                            self.uuid)

    @property
    def public_data_url(self):
        return os.path.join(self.WEBSCANNER_TEST_PUBLIC_DATA_URL,
                            self.uuid)

    @property
    def private_data_path(self):
        if not self.uuid or not self.pk:
            raise self.DoesNotExist('%r is not saved. cannot calculate private_data_path' % self)
        if self.download_path:
            return self.download_path
        return os.path.join(self.WEBSCANNER_TEST_PRIVATE_DATA_PATH,
                            self.uuid)

    def clean_private_data(self):
        '''
        Warning: this method call save
        '''
        res = self.clean_data('private')
        self.is_deleted = True
        self.download_path = None
        self.save()
        return res

    def clean_public_data(self):
        return self.clean_data('public')

    def clean_data(self, dir='public'):
        if dir not in ('public', 'private'):
            raise Exception('You can only remove `public` or `private` dir of test')
        path = getattr(self, '%s_data_path' % dir)

        log.debug('cleaning {!s} data of {!r}...'.format(dir, self))
        if os.path.isdir(path):
            if os.path.basename(path) == self.uuid:
                try:
                    shutil.rmtree(str(path))
                except Exception:
                    log.exception('Cannot remove {!s}'.format(path))
                    return False
                log.info('{!r} {!s} path ({!s}) removed.'.format(self, dir, path))
                return True
            else:
                log.error('{!r} {!s} data path ({!s}) does not contain its uuid, it can remove too much – please check this manually'.format(self, dir, path))
                return False
        else:
            log.warning('{!r} {!s} data path ({!s}) does not exists!'.format(self, dir, path))

    def calculate_rating(self):
        status_multiplier = {RESULT_STATUS.success: 1,
                             RESULT_STATUS.error: 0,
                             RESULT_STATUS.warning: 0.5}
        # we gen only these results that has defined statuses as success,
        # error, warning. info and other statuses are omitted
        results = filter(lambda item: item['status'] in status_multiplier,
                         self.results.all().values('status', 'importance'))
        try:
            return round((sum(status_multiplier[x['status']] * x['importance'] for x in results)\
                          / sum(x['importance'] for x in results)) ** 2 * 10, 2)
        except ZeroDivisionError:
            return 0.0

    def _cache_httrack_request_log(self):
        error_msg = None
        if not self.download_path:
            error_msg = 'path was not set'
        elif not self.download_status == STATUS.success:
            error_msg = 'status is not success'
        elif self.is_deleted:
            error_msg = 'data was deleted'
        if error_msg:
            # if there are any errors, return empty list and not crash whole
            # test
            log.error('Cannot cache httrack log (new.txt) (for %r) because download %s' % (self, error_msg))
            return []

        key = 'scanner.test.%s.httrack:new.txt' % self.uuid
        data = gcache.get(key)
        if not data:
            try:
                data = list(parse_new_txt(os.path.join(
                    self.download_path, 'hts-cache', 'new.txt'), self.download_path))
                gcache.set(key, data)
            except Exception as error:
                log.exception('Error while parsing downloader log.')
                return []
        return data

    @property
    def requests(self):
        return self._cache_httrack_request_log()

    @property
    def downloaded_files(self):
        return [el for el in self._cache_httrack_request_log() if el['size'] > 0 and el['exists']]

    @property
    def url_to_path(self):
        '''URLS to file paths mapping
        '''
        key = 'scanner.test.%s.urls_translation' % self.uuid
        urls_t = lcache.get(key)
        if not urls_t:
            urls_t = {d['url']: d['path'] for d in self.downloaded_files}
            lcache.set(key, urls_t)
        return urls_t

    @property
    def path_to_url(self):
        '''file paths to urls mapping
        '''
        key = 'scanner.test.%s.files_translation' % self.uuid
        files_t = lcache.get(key)
        if not files_t:
            files_t = {d['path']: d['url'] for d in self.downloaded_files}
            lcache.set(key, files_t)
        return files_t




def remove_data_of_a_test_signal(sender, instance, **kwargs):
    log.debug('%r - remove signal' % instance)
    instance.clean_private_data()
    instance.clean_public_data()

pre_delete.connect(remove_data_of_a_test_signal, Tests)


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
    class Meta:
        verbose_name = 'command'
        verbose_name_plural = 'commands'

    test                =   models.ForeignKey(Tests, related_name="commands")
    status              =   models.IntegerField(choices=STATUS, default=STATUS.waiting, db_index=True)
    testname            =   models.CharField(max_length=50, choices=PLUGIN_NAMES)

    run_date            =   models.DateTimeField(default=None,blank=1,null=1)
    finish_date         =   models.DateTimeField(default=None,blank=1,null=1)
    wait_for_download   =   models.BooleanField(default=True, db_index=True)

    objects = CommandQueueManager()

    def __repr__(self):
        return '<CommandQueue pk:{}, name:{}, test:{!r}, status:{!s}>'.format(self.pk,
                                                                              self.testname,
                                                                              self.test,
                                                                              dict(STATUS)[self.status])


    def __unicode__(self):
        return u"%s: status=%s"%(self.test.domain(),unicode(dict(STATUS)[self.status]))


class Results(models.Model):
    class Meta:
        verbose_name = 'result'
        verbose_name_plural = 'results'
    test                =   models.ForeignKey(Tests, related_name="results")

    status              =   models.IntegerField(choices=RESULT_STATUS)
    group               =   models.IntegerField(choices=RESULT_GROUP)
    output_desc         =   models.CharField(max_length=10000)
    output_full         =   models.TextField()

    # used to calculate overal note rank in results (1-5))
    importance          =   models.IntegerField(default=2)

    creation_date       =   models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"%s: %s(%s)"%(self.test.domain(),self.output_desc,unicode(dict(RESULT_STATUS)[self.status]))


#: Model for check_spell plugin to keep 'bad' words (bad, but we want to keep
#: them ;])
class BadWord(models.Model):
    word = models.CharField(max_length=128, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.word

    def __repr__(self):
        return '<{}: {} (seen:{})>'.format(self.__class__.__name__,
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
        bad_words = gcache.get('scanner.bad_words')

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

            gcache.set('scanner.bad_words', bad_words, 60*60*24)

            log.debug('Bad words saved to cache (%d bad words)'%len(bad_words))
            #log.debug(' * %s '%bad_words)
        else:
            log.debug('Bad words loaded from cache (%d)'%len(bad_words))
            #log.debug(' * %s'%bad_words)

        ok_words = list(( w for w in words if w.strip().lower() not in bad_words ))

        return ok_words
