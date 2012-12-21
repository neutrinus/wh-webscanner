
from django.conf.urls.defaults import url, patterns

from addonsapp import views, forms

urlpatterns = patterns('',
    url(r'^contact/?$', views.ContactFormView.as_view(template_name="contact_form/contact.html",
                                             form_class=forms.BasicContactForm,    ),
                                             name="contact"),
    url(r'^contact/completed/?$', views.CompletedPage.as_view(), name="contact_completed"),
)

