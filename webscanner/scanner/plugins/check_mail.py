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
            postmaster = ""
            for mx in mxes:
                try:
                    print str(mx)
                    foo = smtplib.SMTP(str(mx),timeout=5)
                    #if here - connection succesfull
                    foo.set_debuglevel(True)
                    foo.ehlo()
                    (code,msg) = foo.docmd("MAIL","FROM: <mailtest-webscanner@neutrinus.com>")
                    print code
                    print msg
                    (code,msg) = foo.docmd("RCPT","TO: <postmaster@%s>"%(domain))
                    postmaster +=   "<b>mailserver: %s </b><br />&nbsp; RCPT TO: postmaster@%s <br />&nbsp; %s <br /><br />"%(mx,domain,msg)
                    
                    print code
                    print msg
                    
                    foo.quit()
                except smtplib.socket.error:
                    pass    
                
            res = Results(test=command.test)
           
            res.output_desc = unicode(_("mailservers accept postmaster address"))
            res.status = RESULT_STATUS.success
            res.output_full = unicode(_("<p>Details <code>%s</code></p>"%(postmaster ) ))
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
