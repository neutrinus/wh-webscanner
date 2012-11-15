
from django.http import HttpResponseRedirect

class FirstLogin(object):
    '''
    If user log in first time, and he has one test (probably added during
    inline registration), redirect him to results.
    '''

    def process_request(self, request):
        if request.user.is_authenticated():
            profile = request.user.userprofile
            if profile.is_first_login:
                profile.is_first_login = False
                profile.save()
                if request.user.tests_set.all().count() == 1:
                    return HttpResponseRedirect(request.user.tests_set.all()[0].get_absolute_url())
