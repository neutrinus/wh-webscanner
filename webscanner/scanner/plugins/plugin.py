# -*- encoding: utf-8 -*-
__doc__='''
Plugin
========

'''

#from gpanel.scanner.models import STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

class PluginMixin(object):

    def __unicode__(self):
        return unicode(self.name)
    def __str__(self):
        return str(self.name)

    def run(self, command):
        #return (**status**)
        
        raise NotImplemented


