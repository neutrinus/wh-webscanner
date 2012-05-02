# This script do:
#   get list of html file
#   parse them, remove html in several ways, than check language errors 


print 'importing...'
#TODO: zbudowac liste 100 najczesciej pytanych stron z webcheck.me
import sys
import yaml
from time import time

from collections import OrderedDict
try:
    import enchant.checker
    from enchant.tokenize import EmailFilter, URLFilter
except:
    print 'install "pyenchant"'
    sys.exit(1)

#import stripogram # stare
#import transmogrify.htmlcontentextractor as trans # dziwne API

import nltk
import guess_language
import html2text
import chardet
from bs4 import BeautifulSoup
import pytools

#######
# Functions for processing things
#######

class T(object):
    def __init__(self):
        self.widths=[]
        self.rows=[]
        self.headers=[]

    def set_headers(self,iterable):
        self.headers = list(iterable)
        self.widths=[ len(x) for x in self.headers ]

    def add_row(self,iterable):
        i = list(( unicode(x) if not isinstance(x,(str,unicode)) else x for x in iterable))
        while len(i) < len(self.headers):
            i+=[ '--' ]
        row = i[:len(self.headers)]
        self.rows.append( row )
        self.widths = [ max([self.widths[x], len(row[x])]) for x in
                       range(len(self.headers)) ]

    def __unicode__(self):
        ret = ''
        ret += '+'.join(( '='*x for x in self.widths ))
        ret +='\n'
        ret += '|'.join(( self.headers[x].ljust(w) for x,w in
                         enumerate(self.widths)  ))
        ret +='\n'
        ret += '+'.join(( '='*x for x in self.widths ))
        ret +='\n'
        for item in self.rows:
            ret += '|'.join(( item[x].ljust(w) for x,w in
                         enumerate(self.widths)  ))
            ret +='\n'
            ret += '+'.join(( '-'*x for x in self.widths ))
            ret +='\n'

        return ret



########## BS4 STUFF ######################################
def getStrings(root):
   for s in root.childGenerator():
     if hasattr(s, 'name'):    # then it's a tag
       if s.name == 'script':  # skip it!
         continue
       for x in getStrings(s): yield x
     else:                     # it's a string!
       yield s
###########################################################

methods = dict(
    nltk = nltk.clean_html,
#    html2text = html2text.html2text,
    #stripogram = stripogram.html2text, # problems with encoding, extract JS :(

    # extract JS :(, by default, small correctness vvvv
#    bs4 = lambda x:'\n'.join(BeautifulSoup(x).html.body(text=True)),
#    bs4_steroids = lambda x:'\n'.join(getStrings(BeautifulSoup(x).html.body))
)
















####################################################
# START HERE
####################################################

docs = sys.argv[1:] if len(sys.argv)>1 else ['/tmp/www/onet.html']


def check_lang(t):
    code, num, name = guess_language.guessLanguageInfo(t)
    checker = enchant.checker.SpellChecker(code,
                                           filters=[EmailFilter, URLFilter])
    checker.set_text(t)
    return code,[x.word for x in checker ]

def read(filename):
    print 'reading (%s)...'%filename
    f = open(filename).read()
    return f

def decode(text):
    charset = chardet.detect(text)['encoding']
    print 'decoding (%s)...'%charset
    f=text.decode(charset)
    return {'decoded_text':f, 'charset':charset}

def clean(html):
    print 'cleaning html...'
    res = {}
    for meth, fun in methods.items():
        res[meth]={}
        print ' - cleaning with %s'%meth
        start = time()
        res[meth]['cleaned_text']=fun(html)
        stop = time()
        res[meth]['html_clean_time'] = stop-start
    return res
    
def spellcheck(texts):
    print 'spellchecking...'
    result = {}
    for method,data in methods.iteritems():
        result[method]={}
        print ' - spellcheck of %s'%method
        start = time()
        result[method]['lang'], result[method]['errors'] = check_lang(
                                        texts[method]['cleaned_text'])
        stop = time()

        def rem_freq(iter, freq, threshold=3):
            s = set()
            for it, num in freq.iteritems():
                if num <= threshold:
                    s.add(it)
            return s

        result[method]['errors_set'] = set(result[method]['errors'])
        
        llist = list((i.lower() for i in result[method]['errors']))
        result[method]['errors_lower'] = llist

        lset = set((i.lower() for i in result[method]['errors']))
        result[method]['errors_set_lower'] = lset

        dist = nltk.FreqDist(result[method]['errors_lower'])
        result[method]['errors_lower_dist'] = dist

        result[method]['errors_set_lower_rem3'] = rem_freq(lset, dist, 3)
        result[method]['errors_set_lower_rem5'] = rem_freq(lset, dist, 5)
        result[method]['errors_set_lower_rem7'] = rem_freq(lset, dist, 7)

        result[method]['spellcheck_time']=stop-start
    return result


def process_doc(filename):
    stats = dict(filename=filename)
    try:
        text = read(filename)
    except Exception as e:
        print 'DOC %s, reading error: %s'%(filename, e)
        return

    try:
        decoded = decode(text)
    except Exception as e:
        print 'DOC %s, decoding error: %s'%(filename, e)
        return

    stats['text'] = decoded['decoded_text']
    stats['charset']= decoded['charset']

    try:
        clean_html = clean(decoded['decoded_text'])
        stats['clean_html']=clean_html
    except Exception as e:
        print 'DOC %s, cleaning error: %s'%(filename, e)
        return

    try:
        spells = spellcheck(clean_html) 
        stats['spellcheck']=spells
    except Exception as e:
        print 'DOC %s, spellcheck error: %s'%(filename, e)
        return

    return stats

def stats(d):
    print 'STATISTICS for (%s):'%d['filename']
    t = pytools.Table()
    t.add_row([
                'METHOD',
                'lang',
                'enc',
                'clean_len/len',
                'rem freq 3,5,7',
                'err sset',
                'err set',
                'err all',
                'total time'])
    for meth in methods.iterkeys():
        t.add_row([
                    #METHOD
                    meth, 

                      #LANG
                    d['spellcheck'][meth]['lang'],

                    #ENC
                    d['charset'],
                
                    #CLEAN_LEN
                    '%d/%d (%.2f)'%(
                             len(d['clean_html'][meth]['cleaned_text']),
                            len(d['text']),
                            100*len(d['clean_html'][meth]['cleaned_text'])/float(len(d['text'])),
                    
                    ),

                    '%2d, %2d, %2d'%(
                    len(d['spellcheck'][meth]['errors_set_lower_rem3']),
                    len(d['spellcheck'][meth]['errors_set_lower_rem5']),
                    len(d['spellcheck'][meth]['errors_set_lower_rem7']),
                    ),

                    #ERR small
                    len(d['spellcheck'][meth]['errors_set_lower']),
                    #ERR SET
                    len(d['spellcheck'][meth]['errors_set']),
                    #ERR ALL
                    len(d['spellcheck'][meth]['errors']),
                    
                    '(html:%s+sp:%s)=%s'%(
                   '%0.3f'%d['clean_html'][meth]['html_clean_time'],
                   '%0.3f'%d['spellcheck'][meth]['spellcheck_time'],
                   '%0.3f'%(d['clean_html'][meth]['html_clean_time'] \
                   +d['spellcheck'][meth]['spellcheck_time'])
                    )

                  ])
    print t

    
def process_docs(iterable):
    'iterable is list of html filenames'

    docs = list(iterable)
    mr = {} # METHOD RESULTS
    cache={}
    errors = []
    for m in methods.iterkeys():
        ret=dict(
            ratio=0.0,
            rem3=set(),
            rem5=set(),
            rem7=set(),
            errors_lset=set(),
            errors_set=set(),
            errors=[],
            time=0.0,
        )
        for d in docs:
            s = process_doc(d) if d not in cache else cache[d] # return stats
            if d not in cache:
                cache[d]=s
            if not s:
                continue
            stats(s)
            
            errors.extend(s['spellcheck'][m]['errors'])

            ret['ratio'] += 100*len(s['clean_html'][m]['cleaned_text'])/float(len(s['text']))
            ret['errors'].extend(s['spellcheck'][m]['errors'])
            ret['errors_set'].update(s['spellcheck'][m]['errors_set'])
            ret['errors_lset'].update(s['spellcheck'][m]['errors_set_lower'])
            ret['rem3'].update(s['spellcheck'][m]['errors_set_lower_rem3'])
            ret['rem5'].update(s['spellcheck'][m]['errors_set_lower_rem5'])
            ret['rem7'].update(s['spellcheck'][m]['errors_set_lower_rem7'])
            ret['time'] += s['clean_html'][m]['html_clean_time'] \
                   +s['spellcheck'][m]['spellcheck_time']

        for key in ret:
            ret[key] =  len(ret[key])/float(len(docs)) if isinstance(ret[key],
                                           (set,list)) else \
                            ret[key]/float(len(docs))


        mr[m]=ret
    t=T()# pytools.Table()
    print '\n\n\n\n'
    print '==================================================='
    print 'GLOBAL STATISTICS FOR %d DOCUMENTS'%len(docs)
    print '==================================================='
    items = [
        'ratio',
        'rem3',
        'rem5',
        'rem7',
        'errors_lset',
        'errors_set',
        'errors',
        'time',
    ]
    t.set_headers(['METHOD']+items)
    for m, it in mr.iteritems():
        t.add_row([m]+[ it[i] for i in items[:-1] ]+['%0.3f'%it['time']])
    print unicode(t)
    print '---------------------------------------------------'
    print 'Most popular errors:'
    t2 = T()#pytools.Table()
    t2.set_headers(['word','count'])
    for word,count in nltk.FreqDist((e.lower() for e in errors )).items():
        t2.add_row([word,count])

    print unicode(t2)

    import codecs

    errf = codecs.open('errors.txt','w','utf-8')
    errf.write(unicode(t2))
    errf.close()


if __name__ == '__main__':
    process_docs(docs)




