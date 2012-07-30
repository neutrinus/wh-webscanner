# -*- encoding: utf-8 -*-
import os
def apath(x):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))
from decimal import Decimal


DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('neutrinus', 'admin@neutrinus.com'),

)
MANAGERS = ADMINS

ACCOUNT_ACTIVATION_DAYS=1
DEFAULT_FROM_EMAIL = 'noreply@webcheck.me'
EMAIL_HOST='localhost'
EMAIL_PORT=587
EMAIL_HOST_USER='root'
EMAIL_HOST_PASSWORD='xxx'
EMAIL_USE_TLS=False
EMAIL_SUBJECT_PREFIX='[webcheck.me]'

AUTH_PROFILE_MODULE = 'account.UserProfile'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/user/login/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'webcheck',                      # Or path to database file if using sqlite3.
        'USER': 'webcheck',                      # Not used with sqlite3.
        'PASSWORD': 'eepa6aez9OoS',                  # Not used with sqlite3.
        'HOST': '10.239.1.11',                      # Set to empty string for localhost. Not
    }
}

DATABASE_ENGINE = ""

CACHES = {
    'default':{
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ram',
        'TIMEOUT':60*5,
        'OPTIONS':{
            'MAX_ENTRIES':10000,
        },
    }
}

TIME_ZONE = 'Europe/Warsaw'

LANGUAGE_CODE = 'pl'

SHOW_LANGUAGES = ('pl','en')

_ = lambda s:s
LANGUAGES = (
    ('en', _(u'English')),
    ('pl', _(u'Polski')),
    ('de', _(u'Deutsch')),
    ('es', _(u'Español')),
    ('fr', _(u'Français')),
)


LOCALE_PATHS=( apath('locale'), )


SITE_ID = 1

USE_I18N = True
USE_L10N = True

MEDIA_ROOT = apath('media')
STATIC_ROOT = apath('static')

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = (

)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'ju1-hn3r39_!0-9r$9s+om49b!ve*x0pqfvzgn9jbaa2-f7o00'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'djangosecure.middleware.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware', # TEST
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
    'registration',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',

    #apps
    'account',
    'scanner',
    'payments',
    'paypal.standard.ipn',

    #3rd party apps,
    'autoroot',
    'django_extensions',
    'model_utils',
    'djangosecure',
    'django_wsgiserver',
    'crispy_forms',
    'south',

    #testing
    'django_nose',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'verbose': {
            'format': '%(levelname)10s | %(module)10s | %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },

    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter':'verbose',
         },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': 1,
        },
    }
}


# remember to remove old data and check disk usage!
PATH_TMPSCAN = '/tmp/webscanner/'
PATH_OPTIPNG = '/usr/bin/optipng'
SCREENSHOT_SIZE = (1280,1024)

GEOIP_PATH = '/usr/share/GeoIP/GeoLiteCity.dat'

################################
### Third party apps options ###
################################
SECURE_SSL_REDIRECT = 0
SECURE_FRAME_DENY = 1
SECURE_HSTS_SECONDS = 1

SESSION_COOKIE_SECURE=0
SESSION_COOKIE_HTTPONLY =1

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
             '--with-coverage',
             '--cover-tests',
             '--cover-inclusive',
             '--cover-html',
             '--cover-html-dir=html_coverage',
             '--cover-package=scanner',
             '--with-selenium',
             '-v',
             '-s',
             #'--with-profile',
             #'--profile-stats-file=tests/profile',
            ] # arguments to nose for testing

PRODUCT_PRICE = Decimal("9.99")
PAYPAL_RECEIVER_EMAIL = "marek@whitehats.pl"

# This should be at the very end
#execfile(apath('settings_local.py'))
