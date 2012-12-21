#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management import setup_environ
import sys
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')

import webscanner.settings
setup_environ(webscanner.settings)

from multiprocessing import Pool, cpu_count
from webscanner.utils import worker_process, downloader_process, process_wrapper


def main():
    pool = Pool(processes=cpu_count())
    for x in xrange(0, cpu_count()):
        pool.apply_async(worker_process)
        pool.apply_async(downloader_process)
    worker_process()

if __name__ == '__main__':
    process_wrapper(main)
else:
    raise Exception('You should not import this module. It is intendet to run as standalone script only!')
