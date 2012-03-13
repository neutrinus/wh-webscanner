#!/usr/bin/env python
import sys
import os.path as op

def apath(x):
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))

sys.path.insert(0,apath('..'))
sys.path.insert(0,apath('../../'))

from django.core.management import execute_manager
import imp
try:
    imp.find_module('settings') # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import webscanner.settings


if __name__ == "__main__":
    execute_manager(webscanner.settings)
