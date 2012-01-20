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
            reversemxes = ""
            noreversemxes = ""
            for mxdata in answers:
                mxips = dns.resolver.query(mxdata.exchange) 
                #now we have IP
                for ip in mxips:
                    #check if address is not private
                    if IP(ip.address).iptype() == "PRIVATE":
                        records += "%s %s <br>"%(mxdata.exchange,ip)
                                              
                    #check if ip resolves intro FQDN - needed for email
                    try:
                        mx_dnsname = dns.resolver.query(dns.reversename.from_address(ip.address),"PTR")
                        reversemxes += "%s(%s): %s <br />"%(mxdata.exchange,ip.address,mx_dnsname[0])
                    except dns.resolver.NXDOMAIN:
                        noreversemxes += "%s(%s)<br />"%(mxdata.exchange,ip.address)
                    
                    
            res = Results(test=command.test)                
            res.output_desc = unicode(_("No private IP in MX records ") )
            if not records:
                res.output_full = unicode(_("<p>All your MX records are public.</p>" ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                res.status = RESULT_STATUS.error         
            res.save()

            res = Results(test=command.test)                
            res.output_desc = unicode(_("Reverse Entries for MX records") )
            if not noreversemxes:
                res.output_full = unicode(_("<p>All your MX records have reverse records: <code>%s</code></p>"%(reversemxes) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for dont have reverse entries: <code>%s</code>. Folowing MX records have reverse entries: <code>%s</code>. </p>"%(noreversemxes,reversemxes) ))
                res.status = RESULT_STATUS.error         
                
            res.output_full += unicode(_("<p>All mail servers should have a reverse DNS (PTR) entry for each IP address (RFC 1912). Missing reverse DNS entries will make many mailservers to reject your e-mails or mark them as SPAM. </p>"))
            res.save()
            
            
            
            #check DNSBL
            
            # list of blacklists to check
            blacklists      = [
                'sbl-xbl.spamhaus.org',
                'list.dsbl.org',
                'bl.spamcop.net',
                'dnsbl1.dnsbl.borderware.com',
                'dnsbl2.dnsbl.borderware.com',
                'dnsbl.sorbs.net',
                ] 
                
            for bl in blacklists:
                for ipk in mxips:
                    tmp = ipk
                    tmp.split('.') 
                    tmp.reverse()
                    rev_ip = '.'.join(tmp) 
                    querydomain = ip + '.' + bl 
                    try:
                        answers = dns.resolver.query(domain, 'MX')
                        
                    except dns.resolver.NXDOMAIN:
                        
            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception



if __name__ == '__main__':
    main()
