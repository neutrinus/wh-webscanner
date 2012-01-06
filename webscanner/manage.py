#!/usr/bin/env python
import sys
import os.path as op

def apath(x):
    '''
    Sciezki w pythonie odpalane sa wzglednie do miejsca, z ktorego odpalony jest skrypt
    dlatego musza byc podawane absolutne
    '''
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))

sys.path.insert(0,apath('..'))
sys.path.insert(0,apath('../../'))
sys.path.insert(0,apath('../gworker/'))
sys.path.insert(0,apath('../gworker/plugins/'))
sys.path.insert(0,apath('../gpanel/'))

from django.core.management import execute_manager
import imp
try:
    imp.find_module('settings') # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import gpanel.settings


if __name__ == "__main__":
    execute_manager(gpanel.settings)
