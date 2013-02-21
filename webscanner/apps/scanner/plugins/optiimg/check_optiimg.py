#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#import sys
import os
#import random
#import HTMLParser
#import urllib
#import urlparse
#import string
#import logging
import mimetypes
#import shutil

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from django.conf import settings


from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS, RESULT_GROUP

from .utils import ImageOptimizer, CorruptFile


class PluginOptiimg(PluginMixin):
    name = unicode(_('OptiIMG'))
    wait_for_download = True

    OPTIMIZED_IMAGES_DIR_NAME = getattr(settings,
                                        'WEBSCANNER_OPTIIMG_OPTIMIZED_IMAGES_DIR_NAME',
                                        'optimized_images')

    def run(self, command):
        if not command.test.check_performance:
            return STATUS.success

        #domain = command.test.domain
        path = str(command.test.download_path)  # fix UTF-8 path error
        self.log.debug("Recursive check image files size in %s " % path)

        optiimgs = []
        corrupted_imgs = []

        total_bytes_saved = 0

        optimizer = ImageOptimizer()
        optimized_files_path = os.path.join(command.test.public_data_path, self.OPTIMIZED_IMAGES_DIR_NAME)
        optimized_files_url = os.path.join(command.test.public_data_url, self.OPTIMIZED_IMAGES_DIR_NAME)
        if not os.path.exists(optimized_files_path):
            os.makedirs(optimized_files_path)

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)

                #mimetypes is much faster than identify, use it to filterout non-images
                if 'image' not in str(mimetypes.guess_type(file_path)[0]):
                    continue

                self.log.debug("File: %s size: %s" % (file_path, os.path.getsize(file_path)))

                try:
                    optimized_file_path = optimizer.optimize_image(file_path, optimized_files_path)
                except CorruptFile as e:
                    a = {"ifile": file_path[(len(path) + 1):],
                         "error_msg": str(e),
                    }
                    corrupted_imgs.append(a)
                    continue

                if not optimized_file_path:
                    # if optimization was not done correctly or final file
                    # was larger than original
                    continue
                optimized_file_url = os.path.join(optimized_files_url, os.path.basename(optimized_file_path))

                bytes_saved = os.path.getsize(file_path) - os.path.getsize(optimized_file_path)

                self.log.debug("Optimized file is %s (new size: %s)" % (optimized_file_path, os.path.getsize(optimized_file_path)))

                a = {"ifile": file_path[(len(path) + 1):],
                     "ofile": optimized_file_path,
                     "url": optimized_file_url,
                     "ifilesize": os.path.getsize(file_path),
                     "ofilesize": os.path.getsize(optimized_file_path),
                     "bytessaved": bytes_saved,
                     "decrease": (float(bytes_saved) / os.path.getsize(file_path)) * 100,
                     }
                optiimgs.append(a)
                total_bytes_saved += bytes_saved

        template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/msg.html')).read())

        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.performance, importance=2)
        res.output_desc = unicode(_("Images optimalization"))
        res.output_full = template.render(
            Context({'optimized_images': optiimgs, 'total_bytes_saved': total_bytes_saved}))

        if total_bytes_saved < 500 * 1024:
            res.status = RESULT_STATUS.success
        else:
            res.status = RESULT_STATUS.warning
        res.save()


        if corrupted_imgs:
            template = Template(open(os.path.join(os.path.dirname(__file__), 'templates/corrupted.html')).read())
            res = Results(test=command.test, group=RESULT_GROUP.general, importance=3, status=RESULT_STATUS.warning)
            res.output_desc = unicode(_("Images validation"))
            res.output_full = template.render(Context({'corrupted_images': corrupted_imgs}))
            res.save()

        #as plugin finished - its success
        return STATUS.success
