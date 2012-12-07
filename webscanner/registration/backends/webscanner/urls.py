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

)
