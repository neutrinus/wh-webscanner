
from __future__ import absolute_import
import os
import logging

import bs4

from django.conf import settings

import magic
from .file_type_guesser import TextFileTypeGuesser





class Magic(object):

    _cache = None
    _classifier = None

    def __init__(self):
        self.log = logging.getLogger(__name__)

        if not self.__class__._cache:
            self.log.info('Loading MAGIC database')
            self.__class__._cache = magic.Magic(mime=True, magic_file='%s:%s' % (settings.WEBSCANNER_DATABASES['MAGIC']['path'], '/usr/share/misc/magic'))
        if not self.__class__._classifier:
            cls = self.__class__._classifier = TextFileTypeGuesser()
            try:
                cls.load(settings.WEBSCANNER_DATABASES['MIME_TEXT_CLASSIFIER']['path'])
            except Exception as error:
                self.log.exception('Cannot load text file type guesser database.')
                raise


    def magic_for_file(self, file_path):
        if not os.path.exists(file_path):
            raise IOError("File %s not exists." % file_path)
        try:
            mime = self._cache.from_file(file_path)
        except Exception as error:
            self.log.exception('Error while using libmagic for file %s' % file_path)
            return ''
        return mime

    def advanced_for_file(self, file_path):
        mime = self.magic_for_file(file_path)
        if mime.startswith('text') or mime.startswith('application'):
            # This method is not very accurate, some js are parsed as html too
            # :(
            #f = open(file_path).read(2 * 1024 * 1024)
            #try:
            #    x = bs4.BeautifulSoup(f)
            #    x.html.body
            #    return 'text/html'
            #except Exception as error:
            #    print error
            # TODO: try histogram classifier
            if not self._classifier:
                return mime
            mime = self._classifier.guess_from_file(file_path)
        return mime


def preload(source, path, data):
    import glob
    cls = TextFileTypeGuesser()
    ftype = {'html': 'text/html',
             'js': 'application/javascript',
             'css': 'text/css'}
    cls.train({f: ftype[os.path.basename(os.path.dirname(f))] for f in glob.glob(os.path.join(os.path.dirname(__file__), 'file_type_guesser/tests/samples/*/*'))})
    cls.save(path)
