# -*- encoding: utf-8 -*-

from settings import *
def apath(x):
    '''
    Sciezki w pythonie odpalane sa wzglednie do miejsca, z ktorego odpalony jest skrypt
    dlatego musza byc podawane absolutne
    '''
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))

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


#LOGIN_REDIRECT_URL = '/user/account/'
#LOGIN_URL = '/user/login/'



#CACHES = {
    #'default':{
        #'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        #'LOCATION': 'ram',
        #'TIMEOUT':60*5,
        #'OPTIONS':{
            #'MAX_ENTRIES':10000,
        #},
        #'KEY_PREFIX':'webscanner',
    #}
#}



#MIDDLEWARE_CLASSES += (
#    'debug_toolbar.middleware.DebugToolbarMiddleware', # TEST
#)
TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.debug',
)

INSTALLED_APPS += (
    #debugging
    'debug_toolbar',
    'django_wsgiserver',
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
    'INTERCEPT_REDIRECTS': 0,
#    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
#    'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
#    'HIDE_DJANGO_SQL': True,
#    'TAG': 'body',
}

THUMBNAIL_DEBUG=1

SESSION_COOKIE_SECURE=0

