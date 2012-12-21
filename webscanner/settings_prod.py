# -*- encoding: utf-8 -*-
EMAIL_HOST = 'mail.neutrinus.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'noreply@webcheck.me'
EMAIL_HOST_PASSWORD = 'aNi6Aele'
EMAIL_USE_TLS = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'webcheck',
        'USER': 'webcheck',
        'PASSWORD': 'eepa6aez9OoS',
        'HOST': '10.239.1.11',
    }
}

log_conf = {
    'handlers': ['logfile-web-debug'],
    'propagate': 1,
    'level': 'DEBUG',
}

# our namespace
LOGGING["loggers"]["webscanner"] =  log_conf

LOGGING["loggers"]["addonsapp"] =  log_conf
LOGGING["loggers"]["payments"] =  log_conf
LOGGING["loggers"]["account"] =  log_conf
LOGGING["loggers"]["scanner"] =  log_conf
LOGGING["loggers"]["registration_webscanner"] =  log_conf
LOGGING["loggers"]["registration_email"] =  log_conf
LOGGING["loggers"]["registration"] =  log_conf

LOGGING["loggers"]["paypal"] =  log_conf


PAYPAL_CERT_ID = 'HD42YQ3MDRG54'
PAYPAL_RECEIVER_EMAIL = "marek@whitehats.pl"


PATH_TMPSCAN = '/home/webcheck/www/tmp/'


SELENIUM_HUB = "http://sv-seleniumhub:4444/wd/hub"
