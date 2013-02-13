#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import bs4
import mimetypes
from collections import OrderedDict

from scanner.plugins.plugin import PluginMixin
from scanner.models import (STATUS, RESULT_STATUS, RESULT_GROUP)

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


class PluginSEOTags(PluginMixin):

    name = unicode(_('Check SEO tags'))
    wait_for_download = True

    templates = {}

    def check_dirs(self, dirs_paths, rel_path):
        self.log.debug("Search html files in %s " % dirs_paths)

        results = OrderedDict()  # keep order while adding files
        for dir in dirs_paths:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    result = {}
                    file_path = os.path.abspath(os.path.join(root, file))
                    if 'html' not in str(mimetypes.guess_type(file_path)[0]):
                        continue
                    self.log.debug('analizing file %s' % file_path)
                    with open(file_path, 'r') as f:
                        html = bs4.BeautifulSoup(f)

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

                    results[os.path.relpath(file_path, rel_path)] = result
        return results

    def run(self, command):
        from scanner.models import Results
        import glob
        path = str(command.test.download_path)

        # search html files

        dirs = glob.glob(os.path.join(path, '*%s*' % command.test.domain()))

        results = self.check_dirs(dirs, path)

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
        make_result('templates/descriptions.html', _('Meta descriptions'), {'files': results}).save()

        ## Check keywords
        make_result('templates/keywords.html', _('Meta keywords'), {'files': results}, importance=1).save()

        ## Check titles
        make_result('templates/titles.html', _('Pages Titles'), {'files': results}).save()

        #there was no exception - test finished with success
        return STATUS.success
