
import os
import logging
import tempfile
import shutil

import sh

log = logging.getLogger(__name__)


class ImageOptimizer(object):
    def __init__(self, tmp_path=tempfile.gettempdir()):
        '''
        :param tmp_path: tmp for optimizers (some ramdisk path preferable)
        '''
        self.tmp_path = tmp_path

    def mktemp(self, ext=''):
        return tempfile.mktemp(suffix=ext, dir=self.tmp_path)

    @staticmethod
    def select_smallest_file(filelist):
        if len(filelist) == 1:
            return filelist[0]
        o = os.path
        return sorted(filter(lambda f: o.exists(f) and o.getsize(f), filelist),
                      key=lambda f: o.getsize(f))[0]

    @staticmethod
    def optimize_agif(filename, out_filename):
        log.debug('agif optimization...')
        sh.gifsicle('-O2', filename, output=out_filename)

    @staticmethod
    def optimize_jpg(filename, out_filename, progressive=False):
        args = '-optimise', '-copy', 'none',
        if progressive:
            args += '-progressive',
            log.debug('jpeg progressive optimization...')
        else:
            log.debug('jpeg optimization...')
        args += filename,
        sh.jpegtran(*args, _out=out_filename)

    @staticmethod
    def optimize_png_nq(filename, out_filename):
        '''
        pngnq has not `output` parameter, she writes files with specified extensions to the same place.
        '''
        log.debug('png nq optimization...')
        sh.pngnq('-n', '256', '-f', _in=open(filename), _out=out_filename)

    @staticmethod
    def optimize_png_crush(filename, out_filename):
        log.debug('pngcrush optimization...')
        sh.pngcrush('-no_cc', '-rem', 'alla', '-brute', '-l', '9', '-z', '1',
                    '-reduce', '-q', filename, out_filename)

    def optimize_png_mix(self, filename, out_filename):
        tmp_file = self.mktemp()
        self.optimize_png_nq(filename, tmp_file)
        self.optimize_png_crush(tmp_file, out_filename)
        os.unlink(tmp_file)

    @staticmethod
    def convert_gif_to_png(filename, out_filename):
        log.debug('convert gif to png')
        sh.convert(filename, 'png:%s' % out_filename)

    @staticmethod
    def identify_image_type(filename):
        """
        Identify type of image
        """
        try:
            image_type = sh.identify('-format', '%m', filename).strip()
        except sh.ErrorReturnCode:
            log.debug("Cannot identify file %s." % filename)
            return None

        #animated gif produce (GIF)+
        if "GIFGIF" in image_type:
            return "AGIF"
        return image_type

    def optimize_image(self, image_path, out_directory_path):
        '''
        :param image_path: image file path
        :param out_directory_path: file path for optimized image
        :returns: tells the optimization was done or not (if this method
            returns None this means optimization was not done). Otherwise
            it returns path to optimized image.
        :rtype: bool, str

        WARNING: optimized image type can differ from original
        '''
        log.debug('start optimizing file: %s' % image_path)

        img_type = self.identify_image_type(image_path)

        if not img_type:
            log.debug('"%s" image type not recognized')
            return False

        # default output for commands is tmp1
        tmp1 = self.mktemp(os.path.splitext(image_path)[1])
        temp_images_list = [tmp1]

        if img_type == 'JPEG':
            self.optimize_jpg(image_path, tmp1)
            if os.path.getsize(image_path) > 10000:
                # second temp file needed
                tmp2 = self.mktemp(os.path.splitext(image_path)[1])
                temp_images_list.append(tmp2)

                self.optimize_jpg(image_path, tmp2, progressive=True)

        elif img_type == 'PNG':
            self.optimize_png_mix(image_path, tmp1)

        elif img_type == 'GIF':
            self.convert_gif_to_png(image_path, tmp1)

        elif img_type == 'AGIF':
            self.optimize_agif(image_path, tmp1)

        else:
            log.warning('file type: %s - not supported' % img_type)
            #TODO: raise exception is better, but for current interface
            # compatibility this will be fine
            return False

        best_image_path = self.select_smallest_file(temp_images_list)

        # omit best optimized image
        temp_images_list.remove(best_image_path)
        # cleaning not needed files
        for filepath in temp_images_list:
            log.debug('removing unused temp file: %s...' % filepath)
            os.unlink(filepath)

        if not self.identify_image_type(best_image_path):
            log.warning("Optimization goes wrong, final file (%s) has no correct image type! Removing it..." % best_image_path)
            os.unlink(best_image_path)
            return False

        if os.path.getsize(best_image_path) > os.path.getsize(image_path):
            log.debug('Optimized image of "%s" is larger than original. Removing it...' % image_path)
            os.unlink(best_image_path)
            return False
        else:
            log.debug('"%s" optimized successfully')
            new_image_name = os.path.splitext(os.path.basename(image_path))[0] + os.path.splitext(best_image_path)[1]
            new_image_path = os.path.join(out_directory_path, new_image_name)
            shutil.move(best_image_path, new_image_path)
            return new_image_path
