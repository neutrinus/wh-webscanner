#! /usr/bin/env python
# -*- encoding: utf-8 -*-

from urlparse import urlparse
from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _


class PluginUrlLength(PluginMixin):
    name = unicode(_("Check url length"))
    wait_for_download = False

    def run(self, command):
        if not command.test.check_seo:
            return STATUS.success

        from scanner.models import Results
        url = command.test.url

        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=2)
        res.output_desc = unicode(_("URL length") )
        res.output_full = unicode(_("<p>Usability of your website require that url is short and easy to remember. A descriptive URL is better recognized by search engines. A user should be able to look at the address bar (url) and make an accurate guess about the content of the page before entering it (e.g., http://www.company.com/en/products). A SEO strategy should contain a comprehensive policy of URL handling.</p> <p>SEO folks suggest that url should be no longer than 90 characters (and avg should about 75 chars).</p>" ))


        tmpurl = urlparse(command.test.url)
        urllength = len(tmpurl.netloc) + len(tmpurl.path) + len(tmpurl.query)

        if urllength > 80:
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("Your webpage url %s length is <b>%s</b> characters. We suggest not to cross 90 chars border" % (command.test.url, urllength)))
        else:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("Your webpage url %s length is <b>%s</b> characters. Good!" % (command.test.url, urllength)))
        res.save()

        return STATUS.success


if __name__ == '__main__':
    main()
