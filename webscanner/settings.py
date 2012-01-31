# -*- encoding: utf-8 -*-
# Django settings for skaner project.
def apath(x):
    '''
    Sciezki w pythonie odpalane sa wzglednie do miejsca, z ktorego odpalony jest skrypt
    dlatego musza byc podawane absolutne
    '''
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

ACCOUNT_ACTIVATION_DAYS=1
DEFAULT_FROM_EMAIL = 'andrzej.niedzielan@wp.pl'
EMAIL_HOST='smtp.wp.pl'
EMAIL_PORT=587
EMAIL_HOST_USER='andrzej.niedzielan'
EMAIL_HOST_PASSWORD='guardier2012'
EMAIL_USE_TLS=False
EMAIL_SUBJECT_PREFIX='[webscanner]'

LOGIN_REDIRECT_URL = '/user/welcome/'
LOGIN_URL = '/user/login/'

AUTH_PROFILE_MODULE = 'scanner.Profile'
AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'scanner_test1',                      # Or path to database file if using sqlite3.
        'USER': 'skaner',                      # Not used with sqlite3.
        'PASSWORD': 'test7test!@#$',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default':{
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ram',
        'TIMEOUT':60*5,
        'OPTIONS':{
            'MAX_ENTRIES':10000,
        },
#        'KEY_FUNCTION':make_cache_key,
#        'KEY_PREFIX':'guardier',
         
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
LOCALE_PATHS=( apath('locale'), 
             )


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

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.csrf',
    'django.core.context_processors.debug',
)

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
    #our apps
    'scanner',
    'addonsapp',
    #'gpayments',

    #3rd party apps,
    'django_extensions', 
    'model_utils',
    'django_filters',
    'django_tables2',
    'djangosecure',

    #'south',
    #'configstore',
    #'paypal.standard',
    #'paypal.standard.ipn',

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
SCREENSHOT_SIZE = (1280,1024)

################################
### Third party apps options ###
################################

#PAYPAL_RECEIVER_EMAIL = 'tomeks_1317573182_biz@gmail.com'
#PAYPAL_ENCRYPTED = True # post data (for button) should be encrypted?
                        ## require using certificate and key
## GIVE RIGHT ABSOLUTE PATHS TO CERTIFICATES (more info in django-paypal)
#PAYPAL_PRIVATE_CERT = '/path/to/paypal.pem'
#PAYPAL_PUBLIC_CERT = '/path/to/pubpaypal.pem'
#PAYPAL_CERT = '/path/to/paypal_cert.pem'
#PAYPAL_CERT_ID = 'get-from-paypal-website'

THUMBNAIL_DEBUG=0
#THUMBNAIL_ENGINE='sorl.thumbnail.engines.pil_engine.Engine'
THUMBNAIL_ENGINE='sorl.thumbnail.engines.convert_engine.Engine'

SECURE_SSL_REDIRECT = 0
SECURE_FRAME_DENY = 1
SECURE_HSTS_SECONDS = 1

SESSION_COOKIE_SECURE=1
SESSION_COOKIE_HTTPONLY =1


from settings_local import *
