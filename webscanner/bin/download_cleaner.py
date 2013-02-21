#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

import webscanner.settings
setup_environ(webscanner.settings)

from webscanner.utils.processes import download_cleaner_process, process_wrapper


if __name__ == '__main__':
    process_wrapper(download_cleaner_process)
else:
    raise Exception('You should not import this module. It is intendet to run as standalone script only!')
