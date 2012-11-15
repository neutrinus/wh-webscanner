# -*- encoding: utf-8 -*-
import os


EMAIL_HOST='mail.neutrinus.com'
EMAIL_PORT=25
EMAIL_HOST_USER='noreply@webcheck.me'
EMAIL_HOST_PASSWORD='aNi6Aele'
EMAIL_USE_TLS=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'webcheck',                      # Or path to database file if using sqlite3.
        'USER': 'webcheck',                      # Not used with sqlite3.
        'PASSWORD': 'eepa6aez9OoS',                  # Not used with sqlite3.
        'HOST': '10.239.1.11',                      # Set to empty string for localhost. Not
    }
}

PAYPAL_CERT_ID = 'HD42YQ3MDRG54'
PAYPAL_RECEIVER_EMAIL = "marek@whitehats.pl"


PATH_TMPSCAN = '/home/webcheck/www/tmp/'


SELENIUM_HUB = "http://localhost:4444/wd/hub"