from django.conf.urls.defaults import patterns, url

from .forms import WCEmailRegistrationForm


urlpatterns = patterns('',

    # override registration
    url(r'^register/$',
        'registration.views.register',
        {'backend': 'registration.backends.default.DefaultBackend',
         'template_name': 'registration/registration_form.html',
         'form_class': WCEmailRegistrationForm,
        },
        name='registration_register'),

    url(r'^activate/(?P<activation_key>\w+)/$',
        'registration.views.activate',
        {'backend': 'registration_webscanner.backends.webscanner_inline.InlineBackend',
         'template_name': 'registration/activate.html'},
        name='registration_activate'),

)
