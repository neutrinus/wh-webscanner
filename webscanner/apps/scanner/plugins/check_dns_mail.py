#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import re
from urlparse import urlparse

from django.contrib.gis.utils import GeoIP
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from IPy import IP
import dns.resolver
import dns.reversename

from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP
from webscanner.utils.geo import make_map

geoip = GeoIP()


class PluginDNSmail(PluginMixin):
    name = unicode(_("Check dns MAIL"))
    description = unicode(_("Check dns MAIL"))
    wait_for_download = False

    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain()
        test = command.test

        if not command.test.check_mail:
            return STATUS.success
        try:
            mxes = ""
            answers = dns.resolver.query(domain, 'MX')
            for rdata in answers:
                mxes += "MX %s <br>" % (rdata.to_text())
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
                        records += "%s %s <br>" % (mxdata.exchange, ip)

                    #check if ip resolves intro FQDN - needed for email
                    try:
                        mx_dnsname = dns.resolver.query(dns.reversename.from_address(ip.address), "PTR")
                        reversemxes += "%s(%s): %s <br />" % (mxdata.exchange, ip.address, mx_dnsname[0])
                    except dns.resolver.NXDOMAIN:
                        noreversemxes += "%s(%s)<br />" % (mxdata.exchange, ip.address)

            #check geolocation
            locations = {}
            points = []

            for server in answers:
                _temp = locations[str(server.exchange)] = geoip.city(str(server.exchange))
                name = u'%s (%s)' % (_temp['city'], _temp['country_name']) if _temp['city'] else _temp['country_name']
                points.append((float(_temp['longitude']),
                               float(_temp['latitude']),
                               name))
            map_image_filename = 'mailservers_geolocations.png'
            map_image_path = os.path.join(test.public_data_path, map_image_filename)
            map_image_url = os.path.join(test.public_data_url, map_image_filename)
            make_map(points, size=(6, 3), dpi=350 / 3.0, file_path=map_image_path)
            rendered = render_to_string('scanner/serversmap.html', {'locations': locations, 'map_image_url': map_image_url})

            res = Results(test=command.test, group=RESULT_GROUP.performance, importance=1)
            res.output_desc = unicode(_("Mail server(s) geo-location"))
            res.output_full = rendered + unicode(_("<p>Its important to have servers in different geographic locations, to increase reliability of your services.</p>"))
            res.status = RESULT_STATUS.info
            res.save()
            del res

            #check private IPs
            res = Results(test=command.test, group=RESULT_GROUP.mail, importance=5)
            res.output_desc = unicode(_("No private IP in MX records "))
            if not records:
                res.output_full = unicode(_("<p>All your MX records are public.</p>"))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>" % (records)))
                res.status = RESULT_STATUS.error
            res.save()
            del res

            res = Results(test=command.test, group=RESULT_GROUP.mail, importance=3)
            res.output_desc = unicode(_("Reverse Entries for MX records"))
            if not noreversemxes:
                res.output_full = unicode(_("<p>All your MX records have reverse records: <code>%s</code></p>" % (reversemxes)))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Following MX records for dont have reverse entries: <code>%(noreversemxes)s</code>. Folowing MX records have reverse entries: <code>%(reversemxes)s</code>. </p>" % {"noreversemxes": noreversemxes, "reversemxes": reversemxes}))
                res.status = RESULT_STATUS.error

            res.output_full += unicode(_("<p>All mail servers should have a reverse DNS (PTR) entry for each IP address (RFC 1912). Missing reverse DNS entries will make many mailservers reject your e-mails or mark them as SPAM. </p>"))
            res.save()
            del res

            spfrecord = ""
            try:
                answers = dns.resolver.query(domain, 'TXT')
                for rdata in answers:
                    if rdata.strings[0].startswith('v=spf1'):
                        spfrecord += rdata.strings[0]
            except dns.resolver.NoAnswer:
                pass

            res = Results(test=command.test, group=RESULT_GROUP.mail, importance=2)
            res.output_desc = unicode(_("SPF records"))

            res.output_full = "<p>Sender Policy Framework (SPF) is an email validation system designed to prevent email spam by detecting email spoofing, a common vulnerability, by verifying sender IP addresses. SPF allows administrators to specify which hosts are allowed to send mail from a given domain by creating a specific SPF record (or TXT record) in the Domain Name System (DNS). <a href='http://en.wikipedia.org/wiki/Sender_Policy_Framework'>More at wikipedia</a></p>"

            if spfrecord:
                res.output_full += unicode(_("<p>OK, you have SPF record defined: <code>%s</code></p>"%(spfrecord)))
                res.status = RESULT_STATUS.success
            else:
                res.output_full += unicode(_("<p>There is no SPF defined for your domain. Consider creating one - it helps a lot dealing with SPAM.</p>"))
                res.status = RESULT_STATUS.warning
            res.save()
            del res

            return STATUS.success
        except dns.resolver.Timeout,e:
            res = Results(test=command.test, group=RESULT_GROUP.general, importance=3)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>There was timeout while asking your nameservers for MX records.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
            self.log.debug("Timeout while asking for MX records: %s"%str(e))
            del res

        except dns.resolver.NoAnswer,e:
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=4)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>There are no MX records defined for your domain. Having them is essential to be able to recieve emails for this domain.</p>"))

            if re.search("www\.", command.test.url):
                res.output_full += unicode(_(" <div class='alert'>Please try to run this test again <b>without www prefix</b>.</div>" ))
            res.status = RESULT_STATUS.error
            res.save()
            self.log.debug("NoAnswer while asking for MX records: %s"%str(e))
            del res

        except dns.resolver.NXDOMAIN:
            res = Results(test=command.test,group = RESULT_GROUP.general,importance=4)
            res.output_desc = unicode(_("MX records") )
            res.output_full = unicode(_("<p>The query name does not exist. Probably you should define MX entries in your DNS configuration.</p>" ))
            res.status = RESULT_STATUS.error
            res.save()
            self.log.debug("NXDOMAIN while asking for MX records. ")
            del res

        except StandardError,e:
            self.log.exception("%s"%str(e))

        return STATUS.unsuccess

