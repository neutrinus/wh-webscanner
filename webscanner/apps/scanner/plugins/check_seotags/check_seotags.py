#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
import sys
import bs4
import mimetypes

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


class PluginSEOTags(PluginMixin):

    name = unicode(_('Check SEO tags'))
    wait_for_download = True

    def check_title(self, path):
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            return bs4.BeautifulSoup(orig).html.head.findAll('title')

    def check_description(self, path):
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            return bs4.BeautifulSoup(orig).findAll(attrs={"name": "description"})

    def check_keywords(self, path):
        with open(path,'r') as f:
            orig = f.read(self.max_file_size)
            return bs4.BeautifulSoup(orig).findAll(attrs={"name": "keywords"})

    def run(self, command):
        from scanner.models import (Results, CommandQueue)
        import glob
        path = str(command.test.download_path)

        # search html files

        dirs = glob.glob(os.path.join(path,'*%s*'%command.test.domain()))

        self.log.debug("Search html files in %s "%(dirs))

        result_headings = []
        result_keywords = []
        result_descriptions = []
        result_titles = []
        was_errors = False
        for dir in dirs:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))
                    if 'html' not in str(mimetypes.guess_type(file_path)[0]):
                        continue
                    self.log.debug('analizing file %s' % file_path)
                    with open(file_path, 'r') as f:
                        orig = f.read()
                        h1s = bs4.BeautifulSoup(orig).findAll('h1')
                        h2s = bs4.BeautifulSoup(orig).findAll('h2')
                        h2s = bs4.BeautifulSoup(orig).findAll('h2')
                        h3s = bs4.BeautifulSoup(orig).findAll('h3')
                        h4s = bs4.BeautifulSoup(orig).findAll('h4')
                        h5s = bs4.BeautifulSoup(orig).findAll('h5')
                        h6s = bs4.BeautifulSoup(orig).findAll('h6')
                        title = bs4.BeautifulSoup(orig).findAll('title')
                        description = bs4.BeautifulSoup(orig).findAll(attrs={"name": "description"})
                        keywords = bs4.BeautifulSoup(orig).findAll(attrs={"name": "keywords"})

                    result_headings.append({
                        'file': os.path.join(os.path.relpath(file_path,path),),
                        'h1s' : h1s,
                        'h1s_count' : len(h1s),
                        'h2s' : h2s,
                        'h2s_count' : len(h2s),
                        'h3s' : h3s,
                        'h3s_count' : len(h3s),
                        'h4s' : h4s,
                        'h4s_count' : len(h4s),
                        'h5s' : h5s,
                        'h5s_count' : len(h5s),
                        'h6s' : h6s,
                        'h6s_count' : len(h6s),
                    })

                    result_descriptions.append({
                        'file': os.path.join(os.path.relpath(file_path,path),),
                        'description': description,
                        'char_count': len(description),
                    })

                    result_keywords.append({
                        'file': os.path.join(os.path.relpath(file_path,path),),
                        'keywords': keywords,
                    })

                    result_titles.append({
                        'file': os.path.join(os.path.relpath(file_path,path),),
                        'title': title,
                    })

        # Check headings
        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/headings.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=3)
        res.output_desc = unicode(_("Headings"))
        res.output_full = template.render(Context({'files':result_headings,}))
        res.status = RESULT_STATUS.success
        res.save()

        # Check description
        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/descriptions.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.seo,importance=3)
        res.output_desc = unicode(_("Meta desctiption"))
        res.output_full = template.render(Context({'files':result_descriptions,}))
        res.status = RESULT_STATUS.success
        res.save()

        ## Check keywords
        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/keywords.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.seo,importance=1)
        res.output_desc = unicode(_("Meta keywords"))
        res.output_full = template.render(Context({'files':result_keywords,}))
        res.status = RESULT_STATUS.success
        res.save()

        ## Check titles
        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/titles.html')).read())
        res = Results(test=command.test, group = RESULT_GROUP.seo,importance=3)
        res.output_desc = unicode(_("Pages Titles"))
        res.output_full = template.render(Context({'files':result_titles,}))
        res.status = RESULT_STATUS.success
        res.save()

        #there was no exception - test finished with success
        return STATUS.success
