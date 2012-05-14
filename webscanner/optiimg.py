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
    
    

def optimize_jpg(filename):
    
    'jpegtran -outfile "__OUTPUT__" -optimise -copy none %s'%(filename)
    if os.path.getsize(filename) > 10000:
        'jpegtran -outfile "__OUTPUT__" -optimise -progressive "__INPUT__"'

    return [filename]
    
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
        print("File: %s"%(fpath))
        
        if 'image' not in str(mimetypes.guess_type(fpath)[0]):
            continue
        
        filesizes[fpath] = os.path.getsize(fpath)
        
        print identify(fpath)
