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
from django.template.loader import render_to_string


class PluginDNSmail(PluginMixin):
    name = unicode(_("Check dns MAIL"))
    description = unicode(_("Check dns MAIL"))
    wait_for_download = False
    
    def run(self, command):
        from scanner.models import Results
        domain = urlparse(command.test.url).hostname
        

        try:           
            mxes = ""
            answers = dns.resolver.query(domain, 'MX')
            for rdata in answers:
                mxes += "MX %s <br>"%(rdata.to_text() )
                #print 'Host', rdata.exchange, 'has preference', rdata.preference

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
                    
                    
                    
            #check geolocation
            from django.contrib.gis.utils import GeoIP
            from settings import GEOIP_PATH
            geoip = GeoIP()
            locations = {}
                       
            for server in mxips:
                locations[str(server)] = geoip.city(str(server))
            rendered = render_to_string('serversmap.js', {'locations': locations,'id': 'mxserversmap'} )
               
            res = Results(test=command.test,group = RESULT_GROUP.performance, importance=1)
            res.output_desc = unicode(_("Mail server(s) geo-location") )
            res.output_full = rendered + unicode(_("<p>Its important to have servers in different geographic locations, to increase reliability of your services.</p>")) 
            res.status = RESULT_STATUS.info
            res.save()

            res = Results(test=command.test,group = RESULT_GROUP.mail,importance=5)
            res.output_desc = unicode(_("No private IP in MX records ") )
            if not records:
                res.output_full = unicode(_("<p>All your MX records are public.</p>" ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                res.status = RESULT_STATUS.error         
            res.save()

            res = Results(test=command.test,group = RESULT_GROUP.mail,importance=3)
            res.output_desc = unicode(_("Reverse Entries for MX records") )
            if not noreversemxes:
                res.output_full = unicode(_("<p>All your MX records have reverse records: <code>%s</code></p>"%(reversemxes) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for dont have reverse entries: <code>%s</code>. Folowing MX records have reverse entries: <code>%s</code>. </p>"%(noreversemxes,reversemxes) ))
                res.status = RESULT_STATUS.error         
                
            res.output_full += unicode(_("<p>All mail servers should have a reverse DNS (PTR) entry for each IP address (RFC 1912). Missing reverse DNS entries will make many mailservers to reject your e-mails or mark them as SPAM. </p>"))
            res.save()
            

            spfrecord = ""
            try:
                answers = dns.resolver.query(domain, 'TXT')
                for rdata in answers:
                    if rdata.strings[0].startswith('v=spf1'):
                        spfrecord += rdata.strings[0]
            except dns.resolver.NoAnswer:
                pass
                                
            res = Results(test=command.test, group = RESULT_GROUP.mail, importance=2)
            res.output_desc = unicode(_("SPF records") )
            
            res.output_full = "<p>Sender Policy Framework (SPF) is an email validation system designed to prevent email spam by detecting email spoofing, a common vulnerability, by verifying sender IP addresses. SPF allows administrators to specify which hosts are allowed to send mail from a given domain by creating a specific SPF record (or TXT record) in the Domain Name System (DNS). <a href='http://en.wikipedia.org/wiki/Sender_Policy_Framework'>More at wikipedia</a></p>"
                        
            if spfrecord:
                res.output_full += unicode(_("<p>OK, you have SPF record defined: <code>%s</code></p>"%(spfrecord) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full += unicode(_("<p>There is no SPF defined for your domain. Consider creating one - it helps a lot dealing with SPAM.</p>"))
                res.status = RESULT_STATUS.warning
            res.save()
            
            return STATUS.success
        except dns.resolver.Timeout,e:
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=3)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>There was timeout while asking your nameservers for MX records.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
            log.debug("Timeout while asking for MX records: %s"%str(e))
            
        except dns.resolver.NoAnswer,e:
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=4)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>Your nameserver didn't respond (NoAnswer) when asked for MX records.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
            log.debug("NoAnswer while asking for MX records: %s"%str(e))
         
        except dns.resolver.NXDOMAIN:
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=4)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>The query name does not exist. Probably you should define MX entries in your DNS configuration.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
            log.debug("NXDOMAIN while asking for MX records. ")
            
        except StandardError,e:
            log.exception("%s"%str(e))
            
        return STATUS.unsuccess
            



if __name__ == '__main__':
    main()
