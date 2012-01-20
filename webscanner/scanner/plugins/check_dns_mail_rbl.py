#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
import dns.resolver
import dns.reversename
from IPy import IP


import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 


class PluginDNSmailRBL(PluginMixin):
    name = unicode(_("Check dns MAIL RBL"))
    description = unicode(_("Check dns MAIL RBL"))
    
    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain

        # list of blacklists to check
        blacklists      = [
            'dsn.rfc-ignorant.org'
            'bl.spamcop.net',
            'zen.spamhaus.org',
            'dnsbl.sorbs.net',
            ] 
        
        try:           
        
            #ip list of all mail servers
            mxips = []
            answers = dns.resolver.query(domain, 'MX')    
            for mxdata in answers:
                mxips.append(dns.resolver.query(mxdata.exchange)[0].address)
                 
            blacklisted = ""
            notblacklisted = ""
            
            for bl in blacklists:
                for ip in mxips:
                    tmp = str(ip).split('.') 
                    tmp.reverse()
                    rev_ip = '.'.join(tmp) 
                    querydomain = ip + '.' + bl 
                    try:
                        answers = dns.resolver.query(querydomain)
                        blacklisted += "%s listed on %s <br>"%(ip,bl)
                    except dns.resolver.NXDOMAIN:
                        notblacklisted += "%s not listed on %s <br>"%(ip,bl)
                    except dns.resolver.Timeout:
                        log.debug("RBL Timeout: %s while checking: %s"%(bl,ip) )
            
            res = Results(test=command.test)                
            res.output_desc = unicode(_("Mailservers on DNSBL blacklists (RBL)") )
            if not blacklisted:
                res.output_full = unicode(_("<p>None of your mailservers are listed on RBL. We have checked those pairs: <code>%s</code></p>"%(notblacklisted) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Those mailservers are listed on : <code>%s</code>. Folowing MX records have reverse entries: <code>%s</code>. </p>"%(noreversemxes,reversemxes) ))
                res.status = RESULT_STATUS.error         
                
            #res.output_full += unicode(_("<p>All mail servers should have a reverse DNS (PTR) entry for each IP address (RFC 1912). Missing reverse DNS entries will make many mailservers to reject your e-mails or mark them as SPAM. </p>"))
            res.save()
            
            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
