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
import smtplib

import logging
log = logging.getLogger('plugin')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

fh = logging.FileHandler('plugin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh) 


class PluginMail(PluginMixin):
    name = unicode(_('Check mailservers'))
    
    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain

        try:           
            # list of all mail servers
            mxes = []
            answers = dns.resolver.query(domain, 'MX')    
            for mxdata in answers:
                mxes.append(mxdata.exchange)
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception
                        

        try:
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
                    log.debug("Checking mail for MX: %s"%str(mx))
                    
                    #postmaster
                    foo = smtplib.SMTP(str(mx),timeout=5)
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
                    foo = smtplib.SMTP(str(mx),timeout=5)
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
                    foo = smtplib.SMTP(str(mx),timeout=5)
                    #if here - connection succesfull
                    foo.ehlo()
                    (code,msg) = foo.docmd("MAIL","FROM: <mailtest-webscanner@neutrinus.com>")
                    (code,msg) = foo.docmd("RCPT","TO: <openrelaytest-webscanner@neutrinus.com>")
                    if code == 250:
                        openrelay +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: openrelaytest-webscanner@neutrinus.com <br />&nbsp; %s %s <br /><br />"%(mx,code,msg)
                    else:
                        noopenrelay +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: openrelaytest-webscanner@neutrinus.com <br />&nbsp; %s %s <br /><br />"%(mx,code,msg)
                    foo.quit()
                    
                except smtplib.socket.error:
                    noconnect +=   "%s<br />"%(mx)
                    noconnect_count +=1
                    pass    
                
            res = Results(test=command.test)
            res.group = RESULT_GROUP.mail
            res.output_desc = unicode(_("accept mail to postmaster@"))
            res.output_full = unicode(_("<p>According to RFC 822, RFC 1123 and RFC 2821 all mailservers should accept mail to postmaster.</p> "))
            if not nopostmaster:
                res.status = RESULT_STATUS.success
                res.output_full += unicode(_("<p>All of your mailservers accept mail to postmaster@%s: <code>%s</code></p>"%(domain,postmaster ) ))
            else:
                res.status = RESULT_STATUS.warning
                res.output_full += unicode(_("<p>Mailservers that doesnt accept mail to postmaster@%s:<code>%s</code> </p>"%(domain,nopostmaster ) ))
                if postmaster:
                    res.output_full += unicode(_("<p>Mailservers that accept mail to postmaster@%s:<code>%s</code> </p>"%(domain,postmaster ) ))    
            res.save()


            res = Results(test=command.test)
            res.group = RESULT_GROUP.mail
            res.output_desc = unicode(_("accept mail to abuse@"))
            res.output_full = unicode(_("<p>According to RFC 822, RFC 1123 and RFC 2821 all mailservers should accept mail to abuse.</p> "))
            if not noabuse:
                res.status = RESULT_STATUS.success
                res.output_full += unicode(_("<p>All of your mailservers accept mail to abuse@%s: <code>%s</code></p>"%(domain,abuse ) ))
            else:
                res.status = RESULT_STATUS.warning
                res.output_full += unicode(_("<p>Mailservers that doesnt accept mail to abuse@%s:<code>%s</code> </p>"%(domain,noabuse ) ))
                if abuse:
                    res.output_full += unicode(_("<p>Mailservers that accept mail to abuse@%s:<code>%s</code> </p>"%(domain,abuse ) ))    
            res.save()

            
            res = Results(test=command.test)
            res.group = RESULT_GROUP.mail
            res.output_desc = unicode(_("connect to mailservers"))
            res.output_full = unicode(_("<p>Mailservers should accept TCP connections on port 25. Its needed to accept emails from other servers</p> "))
            if not noconnect:                    
                #all servers responds
                res.status = RESULT_STATUS.success
                res.output_full += unicode(_("<p>All of your %s accepted connections</p>"%(len(mxes) ) ))
            elif (noconnect_count< len(mxes)):    
                #some servers didnt respond
                res.status = RESULT_STATUS.warning
                res.output_full += unicode(_("<p>Some(%s) of your %s mailservers didnt accept connection from our check, details:<code>%s</code></p>"%(noconnect_count,len(mxes),noconnect ) ))
            else:
                #none server responded
                res.status = RESULT_STATUS.error
                res.output_full += unicode(_("<p>None of your %s mailservers accepted connection, details: <code>%s</code></p>"%(len(mxes),noconnect ) ))               
            res.save()
            
            res = Results(test=command.test)
            res.group = RESULT_GROUP.mail
            res.output_desc = unicode(_("open-relay check "))
            if not openrelay:
                res.status = RESULT_STATUS.success
                res.output_full += unicode(_("<p>None of your mailservers are open-relays: <code>%s</code></p>"%(noopenrelay ) ))
            else:
                res.status = RESULT_STATUS.error
                res.output_full += unicode(_("<p>Mailservers that are open-relays:<code>%s</code> </p>"%(openrelay ) ))
                if noopenrelay:
                    res.output_full += unicode(_("<p>Mailservers that are not open-relays:<code>%s</code> </p>"%(noopenrelay ) ))    
                    
            res.output_full += unicode(_("<p>Mailservers should not allow relaying, except for authenticated users and trusted IPs.  </p>" ))    
                    
            res.save()
            
            
            
            return STATUS.success
        except StandardError,e:
            log.exception("%s"%str(e))
            return STATUS.exception
            
                        
                        
            #res = Results(test=command.test)                
            #res.output_desc = unicode(_("No private IP in MX records ") )
            #if not records:
                #res.output_full = unicode(_("<p>All your MX records are public.</p>" ))
                #res.status = RESULT_STATUS.success
            #else:
                #res.output_full = unicode(_("<p>Following MX records for this domain are private: <code>%s</code>. Private IP can\'t be rached from the Internet. </p>"%(records) ))
                #res.status = RESULT_STATUS.error         
            #res.save()
