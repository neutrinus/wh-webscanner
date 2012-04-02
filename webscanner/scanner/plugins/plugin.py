# -*- encoding: utf-8 -*-
__doc__='''
Plugin
========

'''

#from gpanel.scanner.models import STATUS
#from django.utils.translation import get_language
#from django.utils.translation import ugettext_lazy as _

class PluginMixin(object):
    '''
    Generic plugin
    '''
    name = unicode(_('Undefined'))
    description = unicode(_("It has no description yet!"))
    
    #wait with worker until webpage is downloaded
    wait_for_download = True
    
    def __unicode__(self):
        return unicode(self.name)
    def __str__(self):
        return str(self.name)

    def run(self, command):
        #return (**status**)
        
        raise NotImplemented


