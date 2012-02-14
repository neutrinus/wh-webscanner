#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from logs import log
import dns.resolver
import urlparse


class PluginSURBL(PluginMixin):
    name = unicode(_("Check SURBL database"))
    wait_for_download = False
    
    
    # Takes the location of the file listing the known TLDs where second level registration is well-known
    # An example of such a file can be downloaded from:
    # http://spamcheck.freeapp.net/two-level-tlds
    def __init__(self):
        f = open("./two-level-tlds")
        self._twoLevelsTlds = f.readlines()
        f.close()
        
    def isMarkedAsSpam(self,uri):
        # The domain part of the URI is the 2nd item in the set
        domainData = urlparse.urlparse(uri)
        registeredName = self._extractRegisteredDomain(domainData[1])
        try:
            answers = dns.resolver.query(registeredName + '.multi.surbl.org', 'A')
            return 1
        except dns.resolver.NXDOMAIN:
            return 0

    def _extractRegisteredDomain(self,authorityComponent):
        import string
        # removing userinfo and port
        #hostComponent = authorityComponent
        hostComponent = "onet.pl"
        dnsParts = string.split(hostComponent,'.')
        secondLevelTld = dnsParts[-2] + '.' + dnsParts[-1] + "\n"
        if (secondLevelTld in self._twoLevelsTlds) and len(dnsParts) > 2:
            registeredName = dnsParts[-3] + '.' + dnsParts[-2] + '.' + dnsParts[-1]
        else:
            registeredName = dnsParts[-2] + '.' + dnsParts[-1]
        return registeredName
    
    
    def run(self, command):
        from scanner.models import Results
        domain = urlparse.urlparse(command.test.url).hostname

        try:    
            res = Results(test=command.test,group = RESULT_GROUP.general, importance=3)
            res.output_desc = unicode(_("<a href='http://www.surbl.org'>SURBL</a> database check") )
            res.output_full = unicode(_("<p>SURBLs are lists of web sites that have appeared in unsolicited messages.</p>" ))
            if self.isMarkedAsSpam(domain):
                res.output_full += unicode(_("<p>Your webpage is <b>listed</b> at SURBL. Check it at <a href='http://www.surbl.org/surbl-analysis'>their site</a> </p>" ))
                res.status = RESULT_STATUS.warning
            else:
                res.output_full += unicode(_("<p>Ok, your webpage is not listed at SURBL.</p>" ))
                res.status = RESULT_STATUS.success         
            res.save()
                
            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
