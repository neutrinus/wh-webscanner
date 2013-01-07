# -*- encoding: utf-8 -*-
import os
DEBUG = True
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': apath('testDataBase.sqlite3'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}
DATABASE_NAME = 'test'

DATABASE_OPTIONS = {'timeout': 200}
CACHES={'default':{
    'BACKEND':'django.core.cache.backends.dummy.DummyCache'
    }}


TEMPLATE_CONTEXT_PROCESSORS += [
    'django.core.context_processors.debug',
]

INSTALLED_APPS += (
    'debug_toolbar',
    'autoroot',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)


#django-debug-toolbar
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': 1,
#    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
#    'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
#    'HIDE_DJANGO_SQL': True,
#    'TAG': 'body',
}

SESSION_COOKIE_SECURE=0
SECURE_SSL_REDIRECT = 0
PAYPAL_CERT_ID = ''
PAYPAL_RECEIVER_EMAIL = "marek_1343638038_biz@whitehats.pl"
PAYPAL_ENCRYPTED = False

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
#EMAIL_FILE_PATH = '/tmp/djangosz'

LOGGING['loggers']['']={
    'handlers':['console','logfile-web-debug'],
    'level':'DEBUG',
    'propagate':1,
}
LOGGING['loggers']['django.db.backends']={
    'level': 'ERROR'}


SELENIUM_HUB = 'http://127.0.0.1:4444/wd/hub'

AUTOROOT_EMAIL='q@q.pl'
