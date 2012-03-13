#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
import dns.resolver
import dns.reversename
from IPy import IP
from urlparse import urlparse
from logs import log

#TODO: add explanationry url
#http://www.spamhaus.org/query/bl?ip=87.206.13.41 
class PluginDNSmailRBL(PluginMixin):
    name = unicode(_("Check dns MAIL RBL"))
    description = unicode(_("Check dns MAIL RBL"))
    wait_for_download = False
    
    def run(self, command):
        from scanner.models import Results
        domain = urlparse(command.test.url).hostname
        

        # list of blacklists to check
        blacklists      = [
            'dsn.rfc-ignorant.org',
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
                 
            results = ""
            blacklisted = 0
            
                
            for ip in mxips:
                for bl in blacklists:
                    tmp = str(ip).split('.') 
                    tmp.reverse()
                    rev_ip = '.'.join(tmp) 
                    querydomain = ip + '.' + bl 
                    try:
                        answers = dns.resolver.query(querydomain)
                        results += "%s <b>listed</b> on %s <br>"%(ip,bl)
                        blacklisted = 1
                    except dns.resolver.NXDOMAIN:
                        results += "%s not listed on %s <br>"%(ip,bl)
                    except dns.resolver.Timeout:
                        log.debug("RBL Timeout: %s while checking: %s"%(bl,ip) )
                results += "<br />"
                        
            
            res = Results(test=command.test, group = RESULT_GROUP.mail, importance=4)
            res.output_desc = unicode(_("Mailservers on DNSBL blacklists (RBL)") )
            if blacklisted == 0:
                res.output_full = unicode(_("<p>None of your mailservers are listed on RBL. Details: <code>%s</code></p>"%(results) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Some of your mailservers are listed on RBL blacklist. Details: <code>%s</code></p> <p> Beeing listed on those lists may cause that your reciptiens will have your mail in SPAM folder</p>"%(results) ))
                res.status = RESULT_STATUS.error         
            res.save()
            
            
            return STATUS.success
        except (dns.resolver.Timeout,dns.resolver.NoAnswer,dns.resolver.NXDOMAIN),e:
            log.debug("dns problem when asking for MX records: %s"%str(e))
            return STATUS.unsuccess
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
