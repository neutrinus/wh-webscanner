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
import shutil 
from time import sleep
from datetime import date
from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from settings import PATH_TMPSCAN
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context


from logs import log


def gentmpfilename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24)) 

def select_smallest_file(filelist):    
    minfile = filelist[0]
    
    for filek in filelist:
        if  (os.path.getsize(filek) >0) and (os.path.getsize(filek) < os.path.getsize(minfile)):
            minfile = filek
            
    return minfile
    
   
def optimize_agif(filename):
    file1 = PATH_TMPSCAN + gentmpfilename()
    files = [filename,file1]
    
    command = 'gifsicle -O2 %s --output %s'%(filename,file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()

    return select_smallest_file(files)


def optimize_jpg(filename):
    file1 = PATH_TMPSCAN +gentmpfilename()
    files = [filename,file1]
    
    command = 'jpegtran -outfile %s -optimise -copy none %s'%(file1,filename)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()

    if os.path.getsize(filename) > 10000:
        file2 = PATH_TMPSCAN +gentmpfilename()
        files.append(file2)
        
        command = 'jpegtran -outfile %s -optimise -progressive %s'%(file2,file1)
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()    
    return select_smallest_file(files)
    
    
def optimize_png(filename):
    file1 = PATH_TMPSCAN +gentmpfilename()
    file2 = PATH_TMPSCAN +gentmpfilename()
    files = [filename,file1, file2]

    shutil.copyfile(filename, file1)

    command =  'pngnq -n 256 -e .png -f %s '%(file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()
    
    command = 'pngcrush -rem alla -brute -reduce -q %s %s'%(file1, file2)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()
    return select_smallest_file(files)
    

def optimize_gif(filename):
    file1 = PATH_TMPSCAN +gentmpfilename()
    #convert it to png and then optimize it as png
    command = 'convert %s png:%s'%(filename,file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()

    flist = [optimize_png(file1), filename]
    
    return select_smallest_file(flist)
    
    

    

    

class PluginOptiimg(PluginMixin):
    name = unicode(_('OptiIMG'))
    wait_for_download = True        


    def identify(self, filename):
        test_command = 'identify -format %%m "%s"'%(filename)

        p = subprocess.Popen(shlex.split(test_command), stdout=subprocess.PIPE)
        (output, stderrdata) = p.communicate()
        
        if p.returncode != 0:
            log.debug("Cannot identify file %s."%filename)
            return False
            
        #animated gif produce (GIF)+
        if "GIFGIF" in str(output):
            output = "AGIF"
            
        return output.strip()
        
        

    
    def run(self, command):
        domain = command.test.domain
        path = command.test.download_path

        log.debug("Recursive check image files size in %s "%(path))
        
        optiimgs = []
        btotals = 0
        
        for root, dirs, files in os.walk(path):
            for file in files:
                fpath = os.path.join(root,file)

                #mimetypes is much faster than identify
                if 'image' not in str(mimetypes.guess_type(fpath)[0]):
                    continue
                
                log.debug("File: %s size: %s"%(fpath, os.path.getsize(fpath)))                
                #filesizes[fpath] = 
                
                ftype = self.identify(fpath)
                
                if ftype == 'JPEG' :
                    ofile = optimize_jpg(fpath)
                elif ftype == 'PNG':
                    ofile = optimize_png(fpath)
                elif ftype == 'GIF':
                    ofile = optimize_gif(fpath)
                elif ftype == 'AGIF':
                    ofile = optimize_agif(fpath)
                else:
                    ofile = None

                if ofile:
                    bytes_saved = os.path.getsize(fpath) - os.path.getsize(ofile)
                    if bytes_saved == 0:
                        continue

                    
                    log.debug("Optimized %s to %s"%(ofile,os.path.getsize(ofile) ))
        

                    a = {   "ifile":fpath[(len(path)+1):],
                            "ofile":ofile[len(PATH_TMPSCAN):],
                            "ifilesize":os.path.getsize(fpath),
                            "ofilesize":os.path.getsize(ofile),
                            "bytessaved":bytes_saved,
                            "decrease": ( float(bytes_saved) / os.path.getsize(fpath) )*100,

                            }                            
                    optiimgs.append(a)
                    btotals += bytes_saved
                   

        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/msg.html')).read())
        
        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.performance,importance=2)
        res.output_desc = unicode(_("Images optimalization"))
        res.output_full = template.render(Context({'optiimgs':optiimgs, 'btotals':btotals}))

        if btotals < 500*1024:
            res.status = RESULT_STATUS.success
        else:
            res.status = RESULT_STATUS.warning
        res.save()
        
        #as plugin finished - its success
        return STATUS.success

