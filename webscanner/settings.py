# -*- encoding: utf-8 -*-
###
# Project specific initialisation
###
import os
import sys


def apath(x):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), x))


sys.path.insert(0, apath('apps'))
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

###
# Django stuff
###

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('neutrinus', 'admin@neutrinus.com'),
)
MANAGERS = (
    ('neutrinus', 'marek@whitehats.pl'),
)

ACCOUNT_ACTIVATION_DAYS = 1
DEFAULT_FROM_EMAIL = 'noreply@webcheck.me'
DEFAULT_SUPPORT_EMAIL = 'support@webcheck.me'
SERVER_EMAIL = 'noreply@webcheck.me'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'root'
EMAIL_HOST_PASSWORD = 'xxx'
EMAIL_USE_TLS = False
EMAIL_SUBJECT_PREFIX = '[webcheck.me]'

AUTH_PROFILE_MODULE = 'account.UserProfile'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/user/login/'

DATABASES = {
}

DATABASE_ENGINE = ""

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ram',
        'TIMEOUT': 60 * 5,
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        },
    }
}
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_MIDDLEWARE_KEY_PREFIX = "ali_"
CACHE_MIDDLEWARE_SECONDS = 60 * 5
CACHE_MIDDLEWARE_ALIAS = "default"

TIME_ZONE = 'Etc/UTC'

LANGUAGE_CODE = 'en'

SHOW_LANGUAGES = ('pl', 'en')

_ = lambda s: s
LANGUAGES = (
    ('en', _(u'English')),
    ('pl', _(u'Polski')),
    ('de', _(u'Deutsch')),
    ('es', _(u'Español')),
    ('fr', _(u'Français')),
)


LOCALE_PATHS = (apath('locale'),)


SITE_ID = 1

USE_I18N = True
USE_L10N = False  # we want to use manual localization

MEDIA_ROOT = apath('media')
STATIC_ROOT = apath('static')

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

AUTHENTICATION_BACKENDS = (
    'registration_email.auth.EmailBackend',
)

STATICFILES_DIRS = (
    apath('assets'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

SECRET_KEY = 'ju1-hn3r39_!0-9r$9s+om49b!ve*x0pqfvzgn9jbaa2-f7o00'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'djangosecure.middleware.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'account.middleware.FirstLogin',
    'account.middleware.CatchNotEnoughCredits',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.csrf',
]

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    apath('templates'),
)

INSTALLED_APPS = (
    #apps

    'account',
    'scanner',
    'payments',
    'addonsapp',
    'registration_webscanner',
    'registration_email',
    'registration',

    'grappelli.dashboard',
    'grappelli',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',


    #3rd party apps,
    'paypal.standard.ipn',
    'django_extensions',
    'model_utils',
    'djangosecure',
    'django_wsgiserver',
    'crispy_forms',
    'infinite_pagination',
    'captcha',
    'spurl',
    'compressor',


    'south',  # keep it as last as possible
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'verbose': {
            'format': '%(levelname)10s | %(name)30s | %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'marek': {
            'format': '%(asctime)s %(name)s(%(process)d) %(levelname)s %(message)s',
        }
    },

    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'logfile-web-debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': apath('logs/webscanner-web-debug.log'),
            'formatter': 'marek',
        },
    },
    'loggers': {
        '': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': 1,
        },
    }
}

#TEST_RUNNER = 'django_pytest.test_runner.TestRunner'

#######################################
### WH webscanner specific settings ###
#######################################

# This variable tells about mounted filesystem which is shared between
# all scanner instances (web, workers, etc)
# - in future, this 'sharing' engine should be replaced by `django-storages`
WEBSCANNER_SHARED_STORAGE = '/tmp/webscanner'

# these path should not be used directly, rather through scanner.models:Tests.private_data_path/public_data_path
WEBSCANNER_TEST_PUBLIC_DATA_PATH = os.path.join(MEDIA_ROOT, 'scan')
WEBSCANNER_TEST_PUBLIC_DATA_URL = os.path.join(MEDIA_URL, 'scan')
WEBSCANNER_TEST_PRIVATE_DATA_PATH = WEBSCANNER_SHARED_STORAGE

WEBSCANNER_TWO_LEVEL_TLDS = open(apath('two-level-tlds')).readlines()

WEBSCANNER_SCREENSHOTS_SELENIUM_BROWSERS = [
    {
        "version": "",
        "browseName": "opera",
        "platform": "LINUX",
    },
    #{
        #"version": "",
        #"browseName": "opera",
        #"platform": "WINDOWS",
    #},
    {
        "version": "",
        "browseName": "chrome",
        "platform": "LINUX",
    },
    #{
        #"version": "",
        #"browseName": "chrome",
        #"platform": "WINDOWS",
    #},
    #{
        #"version": "4.0",
        #"browseName": "firefox",
        #"platform": "WINDOWS",
    #},
    {
        "version": "4.0",
        "browseName": "firefox",
        "platform": "LINUX",
    },
    {
        "version": "7.0",
        "browseName": "firefox",
        "platform": "LINUX",
    },
    #{
        #"version": "7.0",
        #"browseName": "firefox",
        #"platform": "WINDOWS",
    #},
    {
        "version": "10.0",
        "browseName": "firefox",
        "platform": "LINUX",
    },
    #{
        #"version": "10.0",
        #"browseName": "firefox",
        #"platform": "WINDOWS",
    #},
    #{
        #"version": "8",
        #"browseName": "iexplore",
    #},
]

PATH_OPTIPNG = '/usr/bin/optipng'

GEOIP_PATH = '/usr/share/GeoIP/GeoLiteCity.dat'

################################
### Third party apps options ###
################################
SECURE_SSL_REDIRECT = 1
SECURE_FRAME_DENY = 1
SECURE_HSTS_SECONDS = 1

SESSION_COOKIE_SECURE = 1
SESSION_COOKIE_HTTPONLY = 1

RECAPTCHA_PUBLIC_KEY = '6LfmydQSAAAAAOHIqxQaBPr63pMr0XM23ummE4y1'
RECAPTCHA_PRIVATE_KEY = '6LfmydQSAAAAAAU6Wmv9LDHyjnYupYkARmawIQ00 '
RECAPTCHA_USE_SSL = True

PAYPAL_RECEIVER_EMAIL = "marek@whitehats.pl"
PAYPAL_ENCRYPTED = True
PAYPAL_PRIVATE_CERT = apath('paypal.pem')
PAYPAL_PUBLIC_CERT = apath('paypal_pub.pem')
PAYPAL_CERT = apath('paypal_cert.pem')

GRAPPELLI_INDEX_DASHBOARD = 'webscanner.apps.dashboard.CustomIndexDashboard'

COMPRESS_ENABLED = True

# This should be at the very end
WEBSCANNER_ENVIRONMENT = os.environ.get('WEBSCANNER_ENVIRONMENT', '')
print 'WEBSCANNER ENV:',
if WEBSCANNER_ENVIRONMENT.lower() == 'production' or '--production' in sys.argv[1:]:
    print 'PRODUCTION!!!'
    execfile(apath('settings_prod.py'))
elif WEBSCANNER_ENVIRONMENT.lower() in ['test', 'tests', 'testing']:
    print 'automatic tests mode'
    execfile(apath('settings_tests.py'))
else:
    print 'developer mode'
    execfile(apath('settings_local.py'))
    if os.path.exists(apath('settings_private.py')):
        print ' - loading `private settings`'
        execfile(apath('settings_private.py'))
