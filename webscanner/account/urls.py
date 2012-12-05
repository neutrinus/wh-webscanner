# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

#from .forms import EmailRegistrationInlineForm

urlpatterns = patterns('',
    # override django.contrib.auth.urls for logout
    url(r'^logout/$', 'account.views.logout', name='logout'),

    url(r'^', include('registration_email.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),

    url(r'^register/inline/', 
        'account.registration.views.register_inline', 
        {'backend': 'account.registration.backends.inline.InlineBackend',
         'template_name': 'registration/registration_inline.html',
        },
        name='registration_inline'),

)




