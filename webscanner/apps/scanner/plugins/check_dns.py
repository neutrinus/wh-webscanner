#! /usr/bin/env python
# -*- encoding: utf-8 -*-
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP
from django.utils.translation import ugettext_lazy as _
import dns.resolver
from IPy import IP
from urlparse import urlparse

from django.template.loader import render_to_string
from django.contrib.gis.utils import GeoIP

geoip = GeoIP()


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
                records += "A %s <br>" % (rdata.to_text())

            res = Results(test=command.test, group=RESULT_GROUP.general, importance=5)
            res.output_desc = unicode(_("A records (IPv4)"))
            if len(answers) > 1:
                res.output_full = unicode(_("<p>Your nameserver returned %(number)s A records: <code>%(records)s</code></p>" % {
                    "number": len(answers),
                    "records": records
                }))
                res.status = RESULT_STATUS.success
            elif len(answers) == 1:
                res.output_full = unicode(_("<p>Your nameserver returned %(number)s A record: <code>%(records)s</code></p> <p>Having multiple A records with different IP can load-balance traffic.</p>" % {
                    "number": len(answers),
                    "records": records
                }))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>There are none A records for this domain! It means that nobody can reach your website.</p>"))
                res.status = RESULT_STATUS.error
            res.save()
            del records
            del res

            #check geolocation
            locations = {}

            for server in answers:
                locations[str(server.address)] = geoip.city(str(server.address))
            rendered = render_to_string('scanner/serversmap.js', {'locations': locations, 'id': 'webserversmap'})

            res = Results(test=command.test, group=RESULT_GROUP.performance, importance=1)
            res.output_desc = unicode(_("Web server(s) geo-location"))
            # I think webcheck does not show all locations, so information
            # below can be misleading, someone can have a lot of servers
            # already
            res.output_full = rendered + unicode(_("<p>It is important to have servers in different geographic locations, to increase reliability of your services.</p>"))
            res.status = RESULT_STATUS.info
            res.save()
            del locations
            del res

            #check if all IP are public (non-private)
            records = ""
            for rdata in answers:
                if IP(rdata.address).iptype() == "PRIVATE":
                    records += "%s <br" % rdata.address

            res = Results(test=command.test, group=RESULT_GROUP.general, importance=4)
            res.output_desc = unicode(_("No private IP in A records "))
            if not records:
                res.output_full = unicode(_("<p>All your A records are public.</p>"))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following A records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>" % (records)))
                res.status = RESULT_STATUS.error
            res.save()
            del records
            del res

        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            res = Results(test=command.test, group=RESULT_GROUP.general, importance=5)
            res.output_desc = unicode(_("A records (IPv4)"))
            res.output_full = unicode(_("<p><strong>Domain not found!</strong>  Your webpage is currently unreachable, please check your DNS settings, it should consist at least one A record.</p>"))
            res.status = RESULT_STATUS.error
            res.save()
            del res

        #TODO: check AAA (ipv6)

        return STATUS.success
