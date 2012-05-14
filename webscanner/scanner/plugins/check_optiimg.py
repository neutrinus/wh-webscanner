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
from time import sleep
from datetime import date
from plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _


from logs import log

class PluginOptiimg(PluginMixin):
    name = unicode(_('OptiIMG'))
    wait_for_download = True        

    PATH_TMPSCAN = "/tmp/test2/"

    def identify(self, filename):
        test_command = 'identify -format %%m "%s"'%(filename)

        p = subprocess.Popen(shlex.split(test_command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()
        
        if p.returncode != 0:
            print("Cannot identify file.")
            return False
            
        #animated gif produce (GIF)+
        if "GIFGIF" in str(output):
            output = "AGIF"
            
        return output.strip()
        
        
    def gentmpfilename(self):
        return PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) 
    
    def optimize_agif(self, filename):
        file1 = gentmpfilename()
        files = [filename,file1]
        
        command = 'gifsicle -O2 %s --output %s'%(filename,file1)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()

        return files


    def optimize_jpg(self, filename):
        file1 = gentmpfilename()
        files = [filename,file1]
        
        command = 'jpegtran -outfile %s -optimise -copy none %s'%(file1,filename)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()

        if os.path.getsize(filename) > 10000:
            file2 = gentmpfilename()
            files.append(file2)
            
            command = 'jpegtran -outfile %s -optimise -progressive %s'%(file2,file1)
            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
            (output, stderrdata) = p.communicate()    
        return files
        
        
    def optimize_png(self, filename):
        file1 = gentmpfilename()
        file2 = gentmpfilename()
        files = [filename,file1, file2]

    
        command =  'pngnq -n 256 -o %s %s '%(file1,filename)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()
        
        command = 'pngcrush -rem alla -brute -reduce -q %s %s'%(file1, file2)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()
        return files
        
    
    def optimize_gif(self, filename):
        file1 = gentmpfilename()
        #convert it to png and then optimize it as png
        command = 'convert %s png:%s'%(filename,file1)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()

        flist = optimize_png(file1)
        
        flist.append(filename)
        
        return flist
        
        
    def select_smallest_file(self, filelist):
        minfile = filelist[0]
        
        for filek in filelist:
            if os.path.getsize(filek) < os.path.getsize(minfile):
                minfile = filek
        return minfile
        
    
    
    def run(self, command):
        domain = command.test.domain
        path = command.test.download_path

        
        
        log.debug("Recursive check image files size in %s "%(path))
        filesizes = dict()

        for root, dirs, files in os.walk(path):
            for file in files:
                fpath = os.path.join(root,file)
                print("File: %s size: %s"%(fpath, os.path.getsize(fpath)))
                
                #mimetypes is much faster than identify
                if 'image' not in str(mimetypes.guess_type(fpath)[0]):
                    continue
                
                #filesizes[fpath] = 
                
                ftype = identify(fpath)
                
                if ftype == 'JPEG' :
                    ofiles = optimize_jpg(fpath)
                elif ftype == 'PNG':
                    ofiles = optimize_png(fpath)
                elif ftype == 'GIF':
                    ofiles = optimize_gif(fpath)
                elif ftype == 'AGIF':
                    ofiles = optimize_agif(fpath)
                else:
                    ofiles = None

                if ofiles:
                    sfile = select_smallest_file(ofiles)
                    print("Optimized %s to %s"%(sfile,os.path.getsize(sfile) ))
                    
                    #for ofile in ofiles[:1]:
                        #os.remove(ofile)

                        
        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.performance,importance=2)
        res.output_desc = unicode(_("Images (png) optimalization"))
        
            res.status = RESULT_STATUS.warning
            res.output_full = unicode(_("We analized %s files. Some of them may need optimalization: <code>%s</code>"%(fcounter,txtoutput)))
        else:
            res.status = RESULT_STATUS.success
            if fcounter >0:
                res.output_full = unicode(_("All %s png files looks optimized. Good!"%(fcounter)))
            else:
                res.status = RESULT_STATUS.info
                res.output_full = unicode(_("No png files found."))
        res.save()
        
        #as plugin finished - its success
        return STATUS.success

