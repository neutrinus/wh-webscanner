#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
import sys
import bs4


from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


class PluginSEOTags(PluginMixin):

    name = unicode(_('Check SEO tags'))
    wait_for_download = True
    max_file_size = 1024*1024 # in bytes


    def check_headings(self, path):

        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h1s= bs4.BeautifulSoup(orig).findAll('h1')
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h2s= bs4.BeautifulSoup(orig).findAll('h2')
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h3s= bs4.BeautifulSoup(orig).findAll('h3')
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h4s= bs4.BeautifulSoup(orig).findAll('h4')
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h5s= bs4.BeautifulSoup(orig).findAll('h5')
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            h6s= bs4.BeautifulSoup(orig).findAll('h6')

        return {    'h1s': h1s,
                    'h2s': h2s,
                    'h3s': h3s,
                    'h4s': h4s,
                    'h5s': h5s,
                    'h6s': h6s,
                }

    def check_title(self, path):
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            print bs4.BeautifulSoup(orig).findAll('title')

        return None


    def run(self, command):
        from scanner.models import (Results, CommandQueue)
        import glob
        path = str(command.test.download_path)

        # search html files

        dirs = glob.glob(os.path.join(path,'*%s*'%command.test.domain()))

        self.log.debug("Search html files in %s "%(dirs))


        result_headings = []
        was_errors = False
        for dir in dirs:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))

                    headings = self.check_headings(file_path)
                    result_headings.append({
                        'file': os.path.join(os.path.relpath(file_path,path),),
                        'h1s' : headings["h1s"],
                        'h1s_count' : len(headings["h1s"]),
                        'h2s' : headings["h2s"],
                        'h2s_count' : len(headings["h2s"]),
                        'h3s' : headings["h3s"],
                        'h3s_count' : len(headings["h3s"]),
                        'h4s' : headings["h4s"],
                        'h4s_count' : len(headings["h4s"]),
                        'h5s' : headings["h5s"],
                        'h5s_count' : len(headings["h5s"]),
                        'h6s' : headings["h6s"],
                        'h6s_count' : len(headings["h6s"]),
                    })


        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/headings.html')).read())

        res = Results(test=command.test, group = RESULT_GROUP.seo,importance=3)
        res.output_desc = unicode(_("Headings"))
        res.output_full = template.render(Context({'files':result_headings,}))
        res.status = RESULT_STATUS.success
        res.save()





        #there was no exception - test finished with success
        return STATUS.success

