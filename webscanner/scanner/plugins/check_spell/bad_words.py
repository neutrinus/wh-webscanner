
import os
import sys
import time
from datetime import date, datetime
from urlparse import urlparse
import re

# pip require: buzhug
from buzhug import TS_Base as Base

regex = re.compile(r'\w+')

def parse_word(url):
    'returns tuple of words (unicodes)'
    url = urlparse(url)
    words = regex.findall(url.hostname)
    return words

class BadWordsDB(object):
    def __init__(self, path):
        db=self._db = Base(path)
        db.create(
                ('word', str),
                ('time', datetime), # last used
            mode='open')

    def add_word(self, word):
        db.insert(parse_word(word), datetime.now(), 1)

    def add_words(self, words):
        if isinstance(words, basestring):
            words = words.split()
        for word in words:
            self.add_word(word)

    def stats(self, limit=10):
        pass
        
    def close(self):
        self._db.close()

    def __del__(self):
        self._db.close()

if __name__=='__main__':

    for url in examples:
        print 'checking %s'%url

        url_words = parse_item(url)
        print '  - words: %s'%', '.join(url_words)



