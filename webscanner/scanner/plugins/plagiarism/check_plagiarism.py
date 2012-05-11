#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import random
import httplib
from urlparse import urlparse
from scanner.plugins.plugin import PluginMixin
#from scanner.models import UsersTest_Options
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from scanner import pywhois
import random
import HTMLParser
import urllib
import sys
import time
import json
from time import sleep

from logs import log


## 3rd party

import mimetypes
import codecs
import nltk
import bs4
import guess_language

## pip: pyenchant
#import enchant.checker
#from enchant.tokenize import EmailFilter, URLFilter, Filter

## pip: chardet
import chardet







class PluginPlagiarism(PluginMixin):
    '''
    * for each html file:
        * extract text
        * split it intro sentences
        * look for those sentences in [google, yahoo, bing], excluding results from original site
        * count how popular it is
        * measure overall plagiarism rate for file2text
    * output avg plagiarism rate
    
    
    This Plugin uses google API:
    https://developers.google.com/web-search/docs/reference
    to ask for data related to website (number of backlinks, keywords)
    '''
    
    name = unicode(_("plagiarism checker"))
    wait_for_download = True
    max_file_size = 1024*1024 # in bytes


    def file2text(self, path):
        log.debug(' * file: %s'%path)

        # check if file is type of 'html'
        if 'html' not in str(mimetypes.guess_type(path)[0]):
            log.debug('   * is not html file ')
            return None
        else:
            log.debug("   * is html file")

        # read html file and convert it to plain text
        with open(path,'r') as f:
            log.debug("   * opening html file")
            orig = f.read(self.max_file_size) # Max 1 MB of html text file
            log.debug("   * file loaded")
            try:
                charset = chardet.detect(orig)
            except Exception as e:
                charset = {'confidence':0.1, 'encoding':'ascii'}
                log.exception('    * error while detecting charset: %s',e)
            log.debug('    * detected charset: %s'%charset['encoding'])
            if not charset['encoding']:
                log.debug('    * set default encoding (ascii)')
                charset['encoding'] = 'ascii'

            try:
                orig = orig.decode(charset['encoding'])
            except Exception as e:
                log.exception('    * error while decoding text')
                raise CannotDecode(e)

            def strip_script_tags(root):
               for s in root.childGenerator():
                 if hasattr(s, 'name'):    # then it's a tag
                   if s.name == 'script':  # skip it!
                     continue
                   for x in strip_script_tags(s): yield x
                 else:                     # it's a string!
                   yield s

            log.debug('    * cleaning from html to txt')
            try:
                text = '\n'.join(strip_script_tags(
                            bs4.BeautifulSoup(orig).html.body
                ))
            except Exception as e:
                log.info('    * error while cleaning html, omitting file')
                return None

        log.info(' * stop checking file: %s'%path)
        return text

        
    def text2sentences(self, text, lang='en'):
        import nltk.data      
        nltk.download("punkt")
        
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
            
            
        string.splitlines
        print '\n-----\n'.join(tokenizer.tokenize(text))

        
        

    def plagcheck(self, sentence):
        query = urllib.urlencode({'q' : 'link:%s'%(domain)})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&hl=en&%s'%(query)
        search_results = urllib.urlopen(url)
        jdata = json.loads(search_results.read())
        
        if 'estimatedResultCount' not in jdata['responseData']['cursor']:
            log.debug("no estimatedResultCount")
            return STATUS.exception
        
        from scanner.models import Results
        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)
        res.output_desc = unicode(_("google backlinks ") )
        res.output_full = unicode(_('<p>There is about %s sites linking to your site. <a href="%s">See them!</a></p> <p><small>This data is provided by google and may be inaccurate.</small></p> '%(jdata['responseData']['cursor']['estimatedResultCount'], jdata['responseData']['cursor']['moreResultsUrl'] )))
        
    
    
    def run(self, command):
        from scanner.models import (Results, CommandQueue)
        import glob
        path = str(command.test.download_path)

        # search html files
        dirs = glob.glob(os.path.join(path,'*%s*'%command.test.domain()))

        log.debug("Search html files in %s "%(dirs))

        files_with_errors = []
        was_errors = False
        for dir in dirs:
            for root, dirs, files in os.walk(str(dir)):
                for file in files:
                    file_path = os.path.abspath(os.path.join(root, file))
                    log.debug("Check file %s"%(file_path))

                    text = self.file2text(file_path)
                    if not text: 
                        continue
                
                    lang_code, lang_num, lang_name = guess_language.guessLanguageInfo(text)
                    print lang_code
        
                    sentences = self.text2sentences(text, lang_code)
        

        #template = Template(open(os.path.join(os.path.dirname(__file__),
                                              #'templates/msg.html')).read())
        #r = Results(test=command.test,
                    #group=RESULT_GROUP.general,
                    #importance=1,
                    #status=RESULT_STATUS.warning if files_with_errors else\
                           #RESULT_STATUS.success)
        #r.output_desc = unicode(self.name)
        #r.output_full = template.render(Context({'files':files_with_errors}))
        #r.save()

        #if was_errors:
            #return STATUS.unsuccess
        return STATUS.success


