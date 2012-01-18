#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
import dns.resolver
from IPy import IP


import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 


class PluginDNSmail(PluginMixin):
    name = unicode(_("Check dns MAIL"))
    description = unicode(_("Check dns MAIL"))
    
    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain

        try:           
            mxes = ""
            answers = dns.resolver.query(domain, 'MX')
            for rdata in answers:
                mxes += "MX %s <br>"%(rdata.to_text() )
                #print 'Host', rdata.exchange, 'has preference', rdata.preference
                           
            
            res = Results(test=command.test)                
            res.output_desc = unicode(_("MX Records") )
            if len(answers) > 1:
                res.output_full = unicode(_("<p>Your nameserver returned %s MX records: <code>%s</code></p>"%(len(answers),mxes ) ))
                res.status = RESULT_STATUS.success
            elif len(answers) == 1:
                res.output_full = unicode(_("<p>Your nameserver returned %s MX record: <code>%s</code></p> <p> Domains should have at least 2 mailservers, if the primary mailserver is unreachable the secondary will continue to receive domain's e-mails. Although many mailservers will retry to send e-mails up to 3 days, there is a chance that server administrators lowered this interval to a few hours and you may end up loosing your e-mails. </p>"%(len(answers),mxes ) ))
                res.status = RESULT_STATUS.warning
            else:
                res.output_full = unicode(_("<p>There are no MX records for this domain! It means that there is no working email solution.</p>" ))
                res.status = RESULT_STATUS.error         
            res.save()

            
            #check if all IP are public (non-private)
            records = ""
            for mxdata in answers:
                mxips = dns.resolver.query(mxdata.exchange) 
                #now we have IP
                for ip in mxips:
                    if IP(ip).iptype() == "PRIVATE":
                        records += "%s %s <br>"%(mxdata.exchange,ip)
                                              
            
            res = Results(test=command.test)                
            res.output_desc = unicode(_("No private IP in MX records ") )
            if not records:
                res.output_full = unicode(_("<p>All your MX records are public.</p>" ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                res.status = RESULT_STATUS.error         
            res.save()

            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
