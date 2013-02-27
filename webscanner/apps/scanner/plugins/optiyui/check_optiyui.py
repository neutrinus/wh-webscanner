#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import os
from hashlib import sha1

import sh

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context

from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP


yui_compressor = sh.__getattr__('yui-compressor')


class PluginOptiYUI(PluginMixin):
    name = unicode(_('OptiYUI'))
    wait_for_download = True

    OPTIMIZED_CSS_DIR_NAME = getattr(settings,
                                     'WEBSCANNER_OPTIYUI_OPTIMIZED_CSS_DIR_NAME',
                                     'optimized_css')
    OPTIMIZED_JS_DIR_NAME = getattr(settings,
                                    'WEBSCANNER_OPTIYUI_OPTIMIZED_JS_DIR_NAME',
                                    'optimized_js')

    def run(self, command):
        from scanner.models import Results
        if not command.test.check_performance:
            return

        path = str(command.test.download_path)  # fix UTF-8 path problem
        self.log.debug("Recursive check js/css files size in %s " % path)

        optimized_css_path = os.path.join(command.test.public_data_path, self.OPTIMIZED_CSS_DIR_NAME)
        optimized_css_url = os.path.join(command.test.public_data_url, self.OPTIMIZED_CSS_DIR_NAME)

        optimized_js_path = os.path.join(command.test.public_data_path, self.OPTIMIZED_JS_DIR_NAME)
        optimized_js_url = os.path.join(command.test.public_data_url, self.OPTIMIZED_JS_DIR_NAME)

        if not os.path.isdir(optimized_css_path):
            os.makedirs(optimized_css_path)
        if not os.path.isdir(optimized_js_path):
            os.makedirs(optimized_js_path)

        # lists of dicts with file info (see below)
        optimized_files = {'css': [],
                           'js': []}

        total_bytes = {'css': 0,
                       'js': 0}

        total_bytes_saved = {'css': 0,
                             'js': 0}

        for file_info in command.test.downloaded_files:
            file_path = os.path.join(command.test.download_path, file_info['path'])

            mime = file_info['mime'].lower()
            if 'javascript' in mime:
                mime = 'js'
            elif 'text/css' in mime:
                mime = 'css'
            else:
                continue

            file_size = file_info['local_size']

            self.log.debug("File: %s, size:%s, mime:%s" % (file_path, file_size, mime))

            optimized_file_name = '.'.join([sha1(file_path).hexdigest(), mime])
            if mime == 'css':
                optimized_file_path = os.path.join(optimized_css_path, optimized_file_name)
                optimized_file_url = os.path.join(optimized_css_url, optimized_file_name)
            elif mime == 'js':
                optimized_file_path = os.path.join(optimized_js_path, optimized_file_name)
                optimized_file_url = os.path.join(optimized_js_url, optimized_file_name)
            else:
                self.log.error('ASSERTION')
                continue

            try:
                yui_compressor(file_path, type=mime, o=optimized_file_path)
            except Exception:
                self.log.exception('yui-compressor crashed for file %s' % file_path)
                continue

            try:
                optimized_file_size = os.path.getsize(optimized_file_path)
                bytes_saved = file_size - optimized_file_size
            except (IOError, OSError):
                bytes_saved = 0
                self.log.warning('cannot fetch file size of optimized file %s' % optimized_file_path)
                continue

            if bytes_saved < 1:
                self.log.debug('%s was badly optimized (saved %s bytes), no sense to show it' % (optimized_file_path, bytes_saved))
                continue

            try:
                percent_saved = (float(bytes_saved) / file_size) * 100.0
            except ZeroDivisionError:
                percent_saved = 0.0
            optimized_files[mime].append({
                "original_file_url": file_info['url'],
                "original_file_size": file_size,
                "optimized_file_url": optimized_file_url,
                "optimized_file_size": optimized_file_size,
                "bytes_saved": bytes_saved,
                "percent_saved": percent_saved,
            })

            total_bytes[mime] += file_size
            total_bytes_saved[mime] += bytes_saved

        def render_template_for(mime, title, bytes_warning=100 * 1024):
            try:
                total_percent_saved = (float(total_bytes_saved[mime]) / total_bytes[mime]) * 100.0
            except ZeroDivisionError:
                total_percent_saved = 0.0
            ctx = {
                'files': optimized_files[mime],
                'total_bytes': total_bytes[mime],
                'total_bytes_saved': total_bytes_saved[mime],
                'total_percent_saved': total_percent_saved,
            }
            template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/%s.html' % mime)).read())
            res = Results(test=command.test, group=RESULT_GROUP.performance, importance=2)
            res.output_desc = unicode(title)
            res.output_full = template.render(Context(ctx))
            if total_bytes_saved[mime] < bytes_warning:
                res.status = RESULT_STATUS.success
            else:
                res.status = RESULT_STATUS.warning
            res.save()

        render_template_for('js', _("JavaScript optimization"))
        render_template_for('css', _("CSS optimization"), bytes_warning=20 * 1024)

        #as plugin finished - its success
        return STATUS.success
