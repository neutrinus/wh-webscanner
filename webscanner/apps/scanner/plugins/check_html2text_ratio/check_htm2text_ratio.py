#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import os

from django.utils.translation import ugettext_lazy as _

from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP
from webscanner.utils.html import clean_html


class PluginHtml2TextRatio(PluginMixin):
    name = unicode(_('Code to text ratio'))
    wait_for_download = True

    def run(self, command):

        if not command.test.check_seo:
            return

        from scanner.models import Results

        chars_total = 0.0
        chars_text = 0.0
        path = str(command.test.download_path)

        for file_info in command.test.downloaded_files:
            file_path = os.path.join(path, file_info['path'])

            if 'html' not in file_info['mime']:
                continue

            self.log.debug('analizing file %s' % file_path)
            try:
                with open(file_path, 'r') as f:
                    orig = f.read()

                    chars_total += len(orig)
                    chars_text += len(clean_html(orig))
            except (IOError, OSError) as error:
                self.log.warning('error in processing %s: %s' % (file_path, error))
                continue

        try:
            ratio = (chars_text / chars_total) * 100
        except ZeroDivisionError:
            ratio = 0.0

        if ratio == 0.0:
            self.log.warning('probably something goes wrong')
            return STATUS.unsuccess

        res = Results(test=command.test, group=RESULT_GROUP.seo, importance=2)
        res.output_desc = unicode(_("Code to text ratio "))
        res.output_full = unicode(_("<p>The code to text(content) ratio represents the percentage of actual text in your web page. Our software extracts content from website and computes the ratio. Some SEO folks say that perfect ratio should be between 20% and 70%, the others say that this parameter has little to none influence on SEO.</p>"))
        if ratio > 20 and ratio < 70:
            res.status = RESULT_STATUS.success
            res.output_full += unicode(_("<p>Good, your code to text ratio is  <b>%.1f%%</b></p>" % ratio))
        else:
            res.status = RESULT_STATUS.warning
            res.output_full += unicode(_("<p>Your code to text ratio is <b>%.1f%%</b>, maybe you could review content on your website and work on the copy?</p>" % ratio))

        res.save()

        return STATUS.success
