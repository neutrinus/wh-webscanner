# -*- encoding: utf-8 -*-
__doc__='''
Plugin
========

'''

import logging
from django.utils.translation import ugettext_lazy as _

class PluginMixin(object):
    '''
    Generic plugin
    '''
    name = unicode(_('Undefined'))
    description = unicode(_("It has no description yet!"))

    #wait with worker until webpage is downloaded
    wait_for_download = True

    def __init__(self):
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.log.debug('%s plugin initialized' % self.__class__.__name__)

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return str(self.name)

    def run(self, command):
        raise NotImplemented


