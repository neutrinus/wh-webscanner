#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
import dns.resolver
import dns.reversename
from IPy import IP
import smtplib

from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP


class PluginMail(PluginMixin):
    name = unicode(_('Check mailservers'))
    wait_for_download = False

    def run(self, command):

        if not command.test.check_mail:
            return

        from scanner.models import Results
        domain = command.test.domain()

        try:
            # list of all mail servers
            mxes = []
            answers = dns.resolver.query(domain, 'MX')
            for mxdata in answers:
                mxes.append(mxdata.exchange)
        except (dns.resolver.Timeout,dns.resolver.NoAnswer),e:
            self.log.debug("dns problem when asking for MX records: %s"%str(e))
            return STATUS.unsuccess
        except StandardError,e:
            self.log.exception("%s"%str(e))
            return STATUS.exception
        except dns.resolver.NXDOMAIN:
            #log is already produced in check_mail_dns
            return STATUS.exception


        # TODO: keep this in list and then use template to render
        nopostmaster = ""
        postmaster = ""
        noabuse = ""
        abuse = ""
        noconnect = ""
        noconnect_count = 0
        openrelay = ""
        noopenrelay = ""

        for mx in mxes:
            try:
                self.log.debug("Checking mail for MX: %s"%str(mx))

                #postmaster
                foo = smtplib.SMTP(str(mx),timeout=10)
                #if here - connection succesfull
                #foo.set_debuglevel(True)
                foo.ehlo()
                (code,msg) = foo.docmd("MAIL","FROM: <mailtest-webscanner@neutrinus.com>")
                (code,msg) = foo.docmd("RCPT","TO: <postmaster@%s>"%(domain))
                if code == 250:
                    postmaster +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: postmaster@%s <br />&nbsp; %s %s <br /><br />"%(mx,domain,code,msg)
                else:
                    nopostmaster +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: postmaster@%s <br />&nbsp; %s %s <br /><br />"%(mx,domain,code,msg)
                foo.quit()

                #abuse
                foo = smtplib.SMTP(str(mx),timeout=10)
                #if here - connection succesfull
                foo.ehlo()
                (code,msg) = foo.docmd("MAIL","FROM: <mailtest-webscanner@neutrinus.com>")
                (code,msg) = foo.docmd("RCPT","TO: <abuse@%s>"%(domain))
                if code == 250:
                    abuse +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: abuse@%s <br />&nbsp; %s %s <br /><br />"%(mx,domain,code,msg)
                else:
                    noabuse +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: abuse@%s <br />&nbsp; %s %s <br /><br />"%(mx,domain,code,msg)
                foo.quit()

                #openrelay
                foo = smtplib.SMTP(str(mx),timeout=10)
                #if here - connection succesfull
                foo.ehlo()
                (code,msg) = foo.docmd("MAIL","FROM: <mailtest-webscanner@neutrinus.com>")
                (code,msg) = foo.docmd("RCPT","TO: <openrelaytest-webscanner@neutrinus.com>")
                if code == 250:
                    openrelay +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: openrelaytest-webscanner@neutrinus.com <br />&nbsp; %s %s <br /><br />"%(mx,code,msg)
                else:
                    noopenrelay +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: openrelaytest-webscanner@neutrinus.com <br />&nbsp; %s %s <br /><br />"%(mx,code,msg)
                foo.quit()

            except smtplib.SMTPServerDisconnected:
                noconnect +=   "%s (timeout)<br />"%(mx)
                noconnect_count +=1
                pass

            except smtplib.socket.error, smtplib.SMTPConnectError:
                noconnect +=   "%s<br />"%(mx)
                noconnect_count +=1
                pass

        res = Results(test=command.test,group = RESULT_GROUP.mail, importance=1)
        res.output_desc = unicode(_("accept mail to postmaster@"))
        res.output_full = unicode(_("<p>According to RFC 822, RFC 1123 and RFC 2821 all mailservers should accept mail to postmaster.</p> "))

        if not nopostmaster:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>All of your mailservers accept mail to postmaster@%(domain)s: <code>%(postmaster)s</code></p>" % {
                "domain" :domain,
                "postmaster": postmaster
            } ))
        else:
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("<p>Mailservers that do not accept mail to postmaster@%(domain)s:<code>%(nopostmaster)s</code> </p>"% {
                "domain": domain,
                "nopostmaster" :nopostmaster
            } ))
            if postmaster:
                res.output_full += unicode(_("<p>Mailservers that accept mail to postmaster@%(domain)s:<code>%(postmaster)s</code> </p>" % {
                    "domain" : domain,
                    "postmaster" : postmaster
                } ))
        res.save()


        res = Results(test=command.test, group = RESULT_GROUP.mail, importance=1)
        res.output_desc = unicode(_("accept mail to abuse@"))
        res.output_full = unicode(_("<p>According to RFC 822, RFC 1123 and RFC 2821 all mailservers should accept mail to abuse.</p> "))
        if not noabuse:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>All of your mailservers accept mail to abuse@%(domain)s: <code>%(abuse)s</code></p>"% {
                "domain" : domain,
                "abuse" :abuse
            } ))
        else:
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("<p>Mailservers that do not accept mail to abuse@%(domain)s:<code>%(noabuse)s</code> </p>"% {
                "domain": domain,
                "noabuse" :noabuse
            } ))
            if abuse:
                res.output_full += unicode(_("<p>Mailservers that accept mail to abuse@%(domain)s:<code>%(abbuse)s</code> </p>"% {
                    "domain": domain,
                    "abuse" : abuse
                } ))
        res.save()


        res = Results(test=command.test, group = RESULT_GROUP.mail, importance=4)
        res.output_desc = unicode(_("connect to mailservers"))
        res.output_full = unicode(_("<p>Mailservers should accept TCP connections on port 25. It is needed to accept emails from other servers</p> "))
        if not noconnect:
            #all servers responds
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>All of your %s accepted connections</p>"%(len(mxes) ) ))
        elif (noconnect_count< len(mxes)):
            #some servers didnt respond
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("<p>Some(%(noconnect_count)s) of your %(mx_number)s mailservers did not accept connection from our check, details:<code>%(details)s</code></p>"%{"noconnect_count" : noconnect_count, "mx_number":len(mxes), "details" :noconnect } ))
        else:
            #none server responded
            res.status = RESULT_STATUS.error
            res.output_full += unicode(_("<p>None of your %(total_number)s mailservers accepted connection, details: <code>%(code)s</code></p>"% { "total_number" :len(mxes),
                                            "code": noconnect } ))
        res.save()

        res = Results(test=command.test, group = RESULT_GROUP.mail, importance=3)
        res.output_desc = unicode(_("open-relay check "))
        if not openrelay:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>None of your mailservers are open-relays: <code>%s</code></p>"%(noopenrelay ) ))
        else:
            res.status = RESULT_STATUS.error
            res.output_full += unicode(_("<p>Mailservers that are open-relays:<code>%s</code> </p>"%(openrelay)))
            if noopenrelay:
                res.output_full += unicode(_("<p>Mailservers that are not open-relays:<code>%(noopenrelay)s</code> </p>"%dict(noopenrelay=noopenrelay)))

        res.output_full += unicode(_("<p>Mailservers should not allow relaying, except for authenticated users and trusted IPs.  </p>" ))

        res.save()

        return STATUS.success


