from django.utils.translation import ugettext as _

from django.contrib import messages
from django.contrib.auth.views import logout as auth_logout_view

def logout(request):
    messages.info(request, _('You have been logged out. We will miss you!'))
    return auth_logout_view(request)

