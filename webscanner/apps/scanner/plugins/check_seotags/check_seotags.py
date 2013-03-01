#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import bs4
from collections import OrderedDict

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


class PluginSEOTags(PluginMixin):

    name = unicode(_('Check SEO tags'))
    wait_for_download = True

    templates = {}

    def run(self, command):
        from scanner.models import Results
        path = str(command.test.download_path)

        results = OrderedDict()  # keep order while adding files
        for file_info in command.test.downloaded_files:
            file_path = os.path.join(path, file_info['path'])

            result = {}

            if 'html' not in file_info['mime']:
                continue

            self.log.debug('analizing file %s' % file_path)
            try:
                with open(file_path, 'r') as f:
                    html = bs4.BeautifulSoup(f)
            except Exception:
                self.log.exception('Exception while processing file %s' % file_path)
                continue

            try:
                result['title'] = html.head.title.text
            except:
                result['title'] = ''

            try:
                description = html.head.find(attrs={'name': 'description'})
                if description:
                    description = description['content']
                result['description'] = description
            except:
                result['description'] = ''

            try:
                keywords = html.head.find(attrs={"name": "keywords"})
                if keywords:
                    keywords = keywords['content'].split(',')
                result['keywords'] = keywords
            except:
                result['keywords'] = []

            def get_text(iterable):
                return [x.text for x in iterable]

            result['headings'] = OrderedDict()
            for number in range(1, 7):
                try:
                    result['headings']['h%d' % number] = get_text(html.findAll('h%d' % number))
                except:
                    result['headings']['h%d' % number] = []

            results[file_info['url']] = result

        def make_result(template_filename, desc, context, status=RESULT_STATUS.success, importance=3):
            # cache templates
            if not template_filename in self.__class__.templates:
                self.__class__.templates[template_filename] = \
                    Template(open(os.path.join(os.path.dirname(__file__), template_filename)).read())
            template = self.__class__.templates[template_filename]

            res = Results(test=command.test, group=RESULT_GROUP.seo, importance=importance)
            res.output_desc = unicode(desc)
            res.output_full = template.render(Context(context))
            res.status = status
            return res

        # Check headings
        make_result('templates/headings.html', _('Headings'), {'files': results}).save()

        # Check description
        make_result('templates/descriptions.html', _('Meta descriptions'), {'files': results}, importance=2).save()

        ## Check keywords
        make_result('templates/keywords.html', _('Meta keywords'), {'files': results}, importance=1).save()

        ## Check titles
        make_result('templates/titles.html', _('Pages Titles'), {'files': results}).save()

        #there was no exception - test finished with success
        return STATUS.success
