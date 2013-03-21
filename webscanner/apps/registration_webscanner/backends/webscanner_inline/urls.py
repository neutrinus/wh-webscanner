from django.conf.urls.defaults import patterns, url

from .forms import WCEmailRegistrationInlineForm
from .views import register_inline, login_inline
from registration_email.forms import EmailAuthenticationForm

urlpatterns = patterns('',
    # override standard login view to perform login inline (with scan url)
    url(r'^login/$',
        login_inline,
        {'authentication_form': EmailAuthenticationForm},
        name='auth_login'),
    url(r'^register_or_login/$',
        'django.views.generic.simple.direct_to_template',
        {
         'template': 'registration/registration_register_or_login_inline.html',
        },
        name='registration_register_or_login_inline'),
    url(r'^register/inline/$',
        register_inline,
        {'backend': 'registration_webscanner.backends.webscanner_inline.InlineBackend',
         'template_name': 'registration/registration_inline.html',
         'form_class': WCEmailRegistrationInlineForm,
        },
        name='registration_register_inline'),

    url(r'^activate/inline/(?P<activation_key>\w+)/$',
        'registration.views.activate',
        {'backend': 'registration_webscanner.backends.webscanner_inline.InlineBackend',
         'template_name': 'registration/activate.html'},
        name='registration_activate_inline'),

)
