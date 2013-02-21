#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

import webscanner.settings
setup_environ(webscanner.settings)

import time
from multiprocessing import Pool, cpu_count
from webscanner.utils.processes import worker_process, downloader_process, process_wrapper
from webscanner.utils.processes import restarter_process


if __name__ == '__main__':
    process_wrapper(restarter_process)
else:
    raise Exception('You should not import this module. It is intendet to run as standalone script only!')
