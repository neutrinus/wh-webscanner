#!/usr/bin/env python

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


path = "/tmp/test"
PATH_TMPSCAN = "/tmp/test2/"

def identify(filename):
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
    
    
def gentmpfilename():
    return PATH_TMPSCAN + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(24))

def optimize_agif(filename):
    file1 = gentmpfilename()
    files = [filename,file1]
    
    command = 'gifsicle -O2 %s --output %s'%(filename,file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()

    return files


def optimize_jpg(filename):
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
    
    
def optimize_png(filename):
    file1 = gentmpfilename()
    file2 = gentmpfilename()
    files = [filename,file1, file2]
    
    command = 'pngcrush -rem alla -brute -reduce -q %s %s'%(filename, file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()
  
    command =  'pngnq -n 256 -o %s %s '%(file2,file1)
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    (output, stderrdata) = p.communicate()
    return files
    
    
    
    
def select_smallest_file(filelist):
    minfile = filelist[0]
    
    for filek in filelist:
        if os.path.getsize(filek) < os.path.getsize(minfile):
            minfile = filek
    return minfile
        
print("Recursive check image files size in %s "%(path))
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
        elif ftype == 'AGIF':
            ofiles = optimize_agif(fpath)
        else:
            ofiles = None

        if ofiles:
            sfile = select_smallest_file(ofiles)
            print("Optimized %s to %s"%(sfile,os.path.getsize(sfile) ))