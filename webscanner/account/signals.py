
import logging
from django.contrib.auth.signals import user_logged_in

log = logging.getLogger(__name__)

def create_test_during_login(sender, request, user, **kwargs):
    from scanner.models import Tests
    url = request.GET.get('u', None)
    if url is None:
        return
    log.info('creating test during login for %r'%user)
    test = Tests.create_from_signed_url(url, user)
    if test:
        test.start()
        log.info('test created during login (%r) for %r'%(test, user))
    else:
        log.warning('problem with creating test during login: user:%r, sign:%r'%(user, url))

user_logged_in.connect(create_test_during_login)
