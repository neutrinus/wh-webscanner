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

        if not command.test.check_mail:
            return STATUS.success

        from scanner.models import Results
        domain = urlparse(command.test.url).hostname


        # list of blacklists to check
        blacklists = [
            'dsn.rfc-ignorant.org',
            'bl.spamcop.net',
            'zen.spamhaus.org',
            'dnsbl.sorbs.net',
            ]

        dnswl_cat = {
            2 : "Financial services",
            3 : "Email Service Providers",
            4 : "Organisations (both for-profit [ie companies] and non-profit)",
            5 : "Service/network providers",
            6 : "Personal/private servers",
            7 : "Travel/leisure industry",
            8 : "Public sector/governments",
            9 : "Media and Tech companies",
            10 : "some special cases",
            11 : "Education, academic",
            12 : "Healthcare",
            13 : "Manufacturing/Industrial",
            14 : "Retail/Wholesale/Services",
            15 : "Email Marketing Providers",
            255: "unknown",
        }

        dnswl_score = {
            0: "none <small>(only avoid outright blocking)</small>",
            1: "low <small>(reduce chance of false positives)</small>",
            2: "medium <small>(make sure to avoid false positives but allow override for clear cases)</small>",
            3: "high <small>(avoid override)</small>",
            255: "unknown",
        }

        try:
            #ip list of all mail servers
            mxips = []
            answers = dns.resolver.query(domain, 'MX')
            for mxdata in answers:
                mxips.append(dns.resolver.query(mxdata.exchange)[0].address)

            results = ""
            blacklisted = False

            for ip in mxips:
                for bl in blacklists:
                    tmp = str(ip).split('.')
                    tmp.reverse()
                    rev_ip = '.'.join(tmp)
                    querydomain = rev_ip + '.' + bl
                    try:
                        answers = dns.resolver.query(querydomain)
                        results += "%s <b>listed</b> on %s <br>"%(ip,bl)
                        blacklisted = True
                    except dns.resolver.NXDOMAIN:
                        results += "%s not listed on %s <br>"%(ip,bl)
                    except dns.resolver.Timeout:
                        log.debug("RBL Timeout: %s while checking: %s"%(bl,ip) )
                results += "<br />"

            res = Results(test=command.test, group = RESULT_GROUP.mail, importance=4)
            res.output_desc = unicode(_("Mailservers on DNSBL blacklists (RBL)") )
            if not blacklisted:
                res.output_full = unicode(_("<p>None of your mailservers are listed on RBL. Details: <code>%s</code></p>"%(results) ))
                res.status = RESULT_STATUS.success
            else:
                res.output_full = unicode(_("<p>Some of your mailservers are listed on RBL blacklist. Details: <code>%s</code></p> <p> Beeing listed on those lists may cause that your reciptiens will have your mail in SPAM folder</p>"%(results) ))
                res.status = RESULT_STATUS.error
            res.save()

            # whitelist
            results = ""
            whitelisted = False
            for ip in mxips:
                tmp = str(ip).split('.')
                tmp.reverse()
                rev_ip = '.'.join(tmp)
                querydomain = rev_ip + '.list.dnswl.org'
                try:
                    answer = dns.resolver.query(querydomain)[0].address

                    score = dnswl_score[int(answer.split(".")[3])]
                    category = dnswl_cat[int(answer.split(".")[2])]
                    results += "%s listed (score:%s) in category %s<br>"%(ip, score, category)
                    whitelisted = True
                except dns.resolver.NXDOMAIN:
                    results += "%s <b>not listed</b><br>"%(ip)
                except dns.resolver.Timeout:
                    log.debug("DNSWL Timeout: %s while checking: %s"%(bl))

            res = Results(test=command.test, group = RESULT_GROUP.mail, importance=1)
            res.output_desc = unicode(_("Mailservers on DNSWL whitelist"))
            res.output_full = unicode(_("<p>DNSWL is a community driven whitelist of mailservers aiming to prevent false-positives in spam filtering.</p> "))
            if not whitelisted:
                res.output_full += unicode(_("<p>None of your mailservers are listed on <a href='http://www.dnswl.org/'>DNSWL</a>. Details: <code>%s</code></p> <p>Please considier <a href='http://www.dnswl.org/request.pl'>adding</a> your mailservers to DNSWL to improve your success mail delivery rate.</p>"%(results) ))
                res.status = RESULT_STATUS.warning
            else:
                res.output_full += unicode(_("<p>Your mailservers are listed on DNSWL whitelist. Details: <code>%s</code></p>"%(results) ))
                res.status = RESULT_STATUS.success
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
