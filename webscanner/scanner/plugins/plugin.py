# -*- encoding: utf-8 -*-
__doc__='''
Plugin
========

'''

#from gpanel.scanner.models import STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

class PluginMixin(object):
    '''Klasa bazowa dla wszystkich pluginów w systemie.
    
    Chcąc napisać własny plugin powinniśmy odziedziczyć z tej klasy,
    zaimplementwować metody, które nie są zaimplementowane (kod przykładowych
    pluginów w katalogu ``gworker/plugins/``. Aby plugin pojawił się w systemie
    www dodatkowo należy przeczytać i wykonać polecenia z
    ``gpanel.scanner.models`` z sekcji poświęconej pluginom.

    '''

    #: Nazwa pluginu, pokazywana użytkownikowu
    name = _('Unknown plugin')

    #: Krótki opis co to ma robić
    description = _('html description, what that plugin does :)')


    def __unicode__(self):
        return unicode(self.name)
    def __str__(self):
        return str(self.name)

    def run(self, test):
        #return (**status**, **output**)
        
        raise NotImplemented


