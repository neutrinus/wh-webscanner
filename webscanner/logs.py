#!/usr/bin/env python

import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s(%(process)d) %(levelname)s %(message)s')
fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 

