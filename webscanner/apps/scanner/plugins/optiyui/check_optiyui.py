#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import HTMLParser
import urllib
import urlparse
import random
import string
import re
import shlex, subprocess
import mimetypes
import shutil
from time import sleep
from datetime import date
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from django.conf import settings


def gentmpfilename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24))

def select_smallest_file(filelist):
    minfile = filelist[0]

    for filek in filelist:
        if (os.path.exists(filek)) and (os.path.getsize(filek) >0) and (os.path.getsize(filek) < os.path.getsize(minfile)):
            minfile = filek
    return minfile


def optimize_yui(ifile, ftype, output_path, remove_original=False ):

    ofile = settings.PATH_TMPSCAN +gentmpfilename() + "." + ftype
    files = [ifile, ofile]

    command =  'yui-compressor --type %s -o %s %s'%(ftype, ofile, ifile)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()

    ofile = select_smallest_file(files)

    if output_path:
        final_file = output_path + "/" + gentmpfilename() +"." + ftype
        shutil.copyfile(ofile, final_file)

    for filename in files:
        if (filename == ifile):
            continue
        if os.path.exists(filename):
            os.remove(filename)
    if output_path:
        return(final_file)

class PluginOptiYUI(PluginMixin):
    name = unicode(_('OptiYUI'))
    wait_for_download = True

    def run(self, command):

        if not command.test.check_performance:
            return

        domain = command.test.domain
        path = str(command.test.download_path)  # fix UTF-8 path problem
        self.log.debug("Recursive check js/css files size in %s "%(path))

        optifiles = dict()
        optifiles["css"] = []
        optifiles["js"] = []

        btotals = dict()
        btotals["css"] = 0
        btotals["js"] = 0

        for root, dirs, files in os.walk(path):
            for file in files:
                fpath = os.path.join(root,file)

                if mimetypes.guess_type(fpath)[0] == 'application/javascript':
                    ftype = "js"
                elif mimetypes.guess_type(fpath)[0] == 'text/css':
                    ftype = "css"
                else:
                    continue

                self.log.debug("File: %s size: %s"%(fpath, os.path.getsize(fpath)))
                ofile = optimize_yui(fpath, ftype, settings.MEDIA_ROOT+"/", False)

                bytes_saved = os.path.getsize(fpath) - os.path.getsize(ofile)
                if bytes_saved == 0:
                    continue

                self.log.debug("Optimized %s to %s" % (ofile,os.path.getsize(ofile) ))

                optifiles[ftype].append({
                        "ifile": fpath[(len(path)+1):],
                        "ofile": "/" + settings.MEDIA_URL + ofile[len(settings.MEDIA_ROOT+"/")+1:],
                        "ifilesize": os.path.getsize(fpath),
                        "ofilesize": os.path.getsize(ofile),
                        "bytessaved": bytes_saved,
                        "decrease": ( float(bytes_saved) / os.path.getsize(fpath) )*100,
                })
                btotals[ftype] += bytes_saved



        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/js.html')).read())
        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.performance,importance=2)
        res.output_desc = unicode(_("JavaScript optimalization"))
        res.output_full = template.render(Context({'optijses': optifiles["js"], 'btotals':btotals["js"]}))
        if btotals["js"] < 100*1024:
            res.status = RESULT_STATUS.success
        else:
            res.status = RESULT_STATUS.warning
        res.save()

        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/css.html')).read())
        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.performance,importance=2)
        res.output_desc = unicode(_("CSS optimalization"))
        res.output_full = template.render(Context({'opticsses': optifiles["css"], 'btotals':btotals["css"]}))
        if btotals["css"] < 20*1024:
            res.status = RESULT_STATUS.success
        else:
            res.status = RESULT_STATUS.warning
        res.save()


        #as plugin finished - its success
        return STATUS.success
