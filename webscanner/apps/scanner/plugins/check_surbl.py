#! /usr/bin/env python
# -*- encoding: utf-8 -*-
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP
from django.utils.translation import ugettext_lazy as _
import dns.resolver
import urlparse

from webscanner.utils.http import extract_domain, extract_root_domain


class PluginSURBL(PluginMixin):
    name = unicode(_("Check SURBL database"))
    wait_for_download = False

    def isMarkedAsSpam(self, domain):
        # The domain part of the URI is the 2nd item in the set
        registeredName = extract_root_domain(domain)
        try:
            dns.resolver.query(registeredName + '.multi.surbl.org', 'A')
            return True
        except dns.resolver.NXDOMAIN:
            return False

    def run(self, command):
        from scanner.models import Results
        domain = extract_domain(command.test.url)

        res = Results(test=command.test, group=RESULT_GROUP.general, importance=3)
        res.output_desc = unicode(_("<a href='http://www.surbl.org'>SURBL</a> database check"))
        res.output_full = unicode(_("<p>SURBLs are lists of web sites that have appeared in unsolicited messages.</p>"))
        if self.isMarkedAsSpam(domain):
            res.output_full += unicode(_("<p>Your webpage is <b>listed</b> at SURBL. Check it on <a href='http://www.surbl.org/surbl-analysis'>their site</a> </p>"))
            res.status = RESULT_STATUS.warning
        else:
            res.output_full += unicode(_("<p>Ok, your webpage is not listed at SURBL.</p>"))
            res.status = RESULT_STATUS.success
        res.save()

        return STATUS.success
