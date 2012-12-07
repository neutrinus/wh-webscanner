
from django.conf.urls.defaults import patterns, include, url

#from registration_email.backends.default.urls import urlpatterns

urlpatterns = patterns('',
    url(r'^register/inline/$',
        'account.registration.views.register_inline',
        {'backend': 'account.registration.backends.inline.InlineBackend',
         'template_name': 'registration/registration_inline.html',
        },
        name='registration_register_inline'),
    url(r'^activate/inline/(?P<activation_key>\w+)/$',
        #'account.registration.views.activate_inline',
        'registration.views.activate',
        {'backend': 'account.registration.backends.inline.InlineBackend',
         #'template_name': 'registration/activation_inline.html'},
         'template_name': 'registration/activate.html'},
        name='registration_activate_inline'),
)
