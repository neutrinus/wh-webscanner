#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
import httplib

from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP


class PluginRequests(PluginMixin):
    name = unicode(_('Check requests'))
    wait_for_download = True

    def run(self, command):


        from scanner.models import Results
        path = str(command.test.download_path)

        bad_requests = []
        redirects = []
        for request in command.test.requests:
            http_status_code = int(request["http_status_code"])
            request["http_status_code_txt"] =  httplib.responses[http_status_code]
            if not (http_status_code > 199) & (http_status_code < 399) :
                bad_requests.append(request)
            if (http_status_code > 299)  & (http_status_code < 400):
                redirects.append(request)

               #'download_date': data[0],
               #'remote_size': int(sizes[0]),  # httrack remote size
               #'local_size': int(sizes[1]),  # httrack local size
               #'flags': data[2],
               #'http_status_code': data[3],
               #'status': data[4],
               #'httrack_mime': data[5],  # httrack mime type
               #'etag': data[6],
               #'url': data[7],
               #'path': os.path.relpath(data[8], root_path) if root_path else data[8],
               #'from_url': data[9],
               #'mime': type,
               #'size': size,
               #'exists':

        template = Template(open(os.path.join(os.path.dirname(__file__),
                                            'templates/bad_requests.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.security, importance=4)
        res.output_desc = unicode(_("HTTP problems"))
        if bad_requests:
            res.status = RESULT_STATUS.error
        else:
            res.status = RESULT_STATUS.success
        res.output_full = template.render(Context({'bad_requests': bad_requests}))
        res.save()


        template = Template(open(os.path.join(os.path.dirname(__file__),
                                            'templates/redirects.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.performance, importance=2)
        res.output_desc = unicode(_("Redirects"))
        if len(redirects) > 5:
            res.status = RESULT_STATUS.warning
        else:
            res.status = RESULT_STATUS.info

        res.output_full = template.render(Context({'redirects': redirects, 'rnumber': len(redirects)}))
        res.save()

        return STATUS.success


