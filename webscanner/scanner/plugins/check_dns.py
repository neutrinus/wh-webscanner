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
from urlparse import urlparse
from logs import log

from django.template.loader import render_to_string



class PluginDNS(PluginMixin):
    name = unicode(_("Check dns"))
    description = unicode(_("Check dns"))
    wait_for_download = False
    
    
    def run(self, command):
        from scanner.models import Results
        domain = urlparse(command.test.url).hostname

        try:
            #A
            records = ""
            answers = dns.resolver.query(domain, 'A')
            for rdata in answers:
                records += "A %s <br>"%(rdata.to_text() )
                        
            
            res = Results(test=command.test,group = RESULT_GROUP.general, importance=5)
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

            #check geolocation
            from django.contrib.gis.utils import GeoIP
            from settings import GEOIP_PATH
            geoip = GeoIP()
            locations = {}
                        
            for server in answers:
                locations[str(server.address)] = geoip.city(str(server.address))
                
            for x in locations:
                print(locations[x]['latitude'])

            rendered = render_to_string('serversmap.js', {'locations': locations})
                
            res = Results(test=command.test,group = RESULT_GROUP.general, importance=1)
            res.output_desc = unicode(_("Web server(s) geo-location") )
            res.output_full = rendered + unicode(_("<p>Its important to have servers in different geographic locations, to increase reliability of your services.</p>")) 
            res.status = RESULT_STATUS.info
            res.save()

            
            #check if all IP are public (non-private)
            records = ""
            for rdata in answers:
                if IP(rdata.address).iptype() == "PRIVATE":
                    records += "%s <br"%rdate.address
            
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=4)                
            res.output_desc = unicode(_("No private IP in A records ") )
            if not records:
                res.output_full = unicode(_("<p>All your A records are public.</p>" ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following A records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                res.status = RESULT_STATUS.error    
            res.save()
            
        except dns.resolver.NXDOMAIN:
            res = Results(test=command.test,group = RESULT_GROUP.general, importance=5)
            res.output_desc = unicode(_("A records (IPv4)") )
            res.output_full = unicode(_("<p>Domain not found!.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
        
        #TODO: check AAA (ipv6)
        
        return STATUS.success



if __name__ == '__main__':
    main()
