#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
import dns.resolver
from IPy import IP

from logs import log


class PluginDNS(PluginMixin):
    name = unicode(_("Check dns"))
    description = unicode(_("Check dns"))
    wait_for_download = False
    
    
    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain

        try:    
        
            try:
                #A
                records = ""
                answers = dns.resolver.query(domain, 'A')
                for rdata in answers:
                    records += "A %s <br>"%(rdata.to_text() )
                            
                
                res = Results(test=command.test)
                res.group = RESULT_GROUP.general

                res.output_desc = unicode(_("A records (IPv4)") )
                if len(answers) > 1:
                    res.output_full = unicode(_("<p>Your nameserver returned %s A records: <code>%s</code></p>"%(len(answers),records ) ))
                    res.status = RESULT_STATUS.success
                elif len(answers) == 1:
                    res.output_full = unicode(_("<p>Your nameserver returned %s A record: <code>%s</code></p> <p>Having multiple A records with different IP can load-balance traffic.</p>"%(len(answers),records ) ))
                    res.status = RESULT_STATUS.success
                else:
                    res.output_full = unicode(_("<p>There are no A records for this domain! It means that nobody can reach your website.</p>" ))
                    res.status = RESULT_STATUS.error         
                res.save()

                #check if all IP are public (non-private)
                records = ""
                for rdata in answers:
                    if IP(rdata.address).iptype() == "PRIVATE":
                        records += "%s <br"%rdate.address
                
                res = Results(test=command.test)                
                res.group = RESULT_GROUP.general
                res.output_desc = unicode(_("No private IP in A records ") )
                if not records:
                    res.output_full = unicode(_("<p>All your A records are public.</p>" ))
                    res.status = RESULT_STATUS.success
                else:
                    res.output_full = unicode(_("<p>Following A records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                    res.status = RESULT_STATUS.error    
                res.save()
                
            except dns.resolver.NXDOMAIN:
                res = Results(test=command.test)                
                res.group = RESULT_GROUP.general
                res.output_desc = unicode(_("A records (IPv4)") )
                res.output_full = unicode(_("<p>Domain not found!.</p>" ))
                res.status = RESULT_STATUS.error
                res.save()
            except StandardError,e:
                log.exception("During check A record: %s"%str(e))
            
            #try:
                ##AAA
                #records = ""
                #answers = dns.resolver.query(domain, 'AAA')
                #for rdata in answers:
                    #records += "AAA %s <br>"%(rdata.to_text() )
                            
                
                #res = Results(test=command.test)                
                #res.output_desc = unicode(_("AAA records (IPv6)") )
                #if len(answers) > 1:
                    #res.output_full = unicode(_("<p>Your nameserver returned %s AAA records: <code>%s</code></p>"%(len(answers),records ) ))
                    #res.status = RESULT_STATUS.success
                #elif len(answers) == 1:
                    #res.output_full = unicode(_("<p>Your nameserver returned %s AAA record: <code>%s</code></p> <p>Having multiple AAA records with different IP can load-balance traffic.</p>"%(len(answers),records ) ))
                    #res.status = RESULT_STATUS.success
                #else:
                    #res.output_full = unicode(_("<p>There are no AAA records for this domain! It means that probably your site is not IPv6 compatibile.</p>" ))
                    #res.status = RESULT_STATUS.warning         
                #res.save()
            
            #except StandardError,e:
                #log.exception("During check AAA record: %s"%str(e))
                
            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
