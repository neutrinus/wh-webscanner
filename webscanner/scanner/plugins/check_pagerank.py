#! /usr/bin/env python
# -*- encoding: utf-8 -*-
#  Script for getting Google Page Rank of page
#  Google Toolbar 3.0.x/4.0.x Pagerank Checksum Algorithm
#
#  original from http://pagerank.gamesaga.net/
#  this version was adapted from http://www.djangosnippets.org/snippets/221/
#  by Corey Goldberg - 2010
#
#  Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php


import sys
import os
import re
import urllib2
import urllib

from plugin import PluginMixin
from scanner.models import STATUS, RESULT_STATUS,RESULT_GROUP
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from logs import log
 
 
def get_pagerank(url):
    hsh = check_hash(hash_url(url))
#    gurl = 'http://www.google.com/search?client=navclient-auto&features=Rank:&q=info:%s&ch=%s' % (urllib.quote(url), hsh)
    gurl = 'http://toolbarqueries.google.com/tbr?client=navclient-auto&ch=' + hsh + '&features=Rank&q=info:' +url+'&num=100&filter=0';
    try:
        f = urllib.urlopen(gurl)
        rank = f.read().strip()[9:]
    except Exception:
        rank = 'N/A'
    if rank == '':
        rank = '0'
    return rank
 
 
def  int_str(string, integer, factor):
    for i in range(len(string)) :
        integer *= factor
        integer &= 0xFFFFFFFF
        integer += ord(string[i])
    return integer
 
 
def hash_url(string):
    c1 = int_str(string, 0x1505, 0x21)
    c2 = int_str(string, 0, 0x1003F)
 
    c1 >>= 2
    c1 = ((c1 >> 4) & 0x3FFFFC0) | (c1 & 0x3F)
    c1 = ((c1 >> 4) & 0x3FFC00) | (c1 & 0x3FF)
    c1 = ((c1 >> 4) & 0x3C000) | (c1 & 0x3FFF)
 
    t1 = (c1 & 0x3C0) << 4
    t1 |= c1 & 0x3C
    t1 = (t1 << 2) | (c2 & 0xF0F)
 
    t2 = (c1 & 0xFFFFC000) << 4
    t2 |= c1 & 0x3C00
    t2 = (t2 << 0xA) | (c2 & 0xF0F0000)
 
    return (t1 | t2)
 
 
def check_hash(hash_int):
    hash_str = '%u' % (hash_int)
    flag = 0
    check_byte = 0
 
    i = len(hash_str) - 1
    while i >= 0:
        byte = int(hash_str[i])
        if 1 == (flag % 2):
            byte *= 2;
            byte = byte / 10 + byte % 10
        check_byte += byte
        flag += 1
        i -= 1
 
    check_byte %= 10
    if 0 != check_byte:
        check_byte = 10 - check_byte
        if 1 == flag % 2:
            if 1 == check_byte % 2:
                check_byte += 9
            check_byte >>= 1
 
    return '7' + str(check_byte) + hash_str
 
 
 

def get_alexa_rank(url):
    try:
        data = urllib2.urlopen('http://data.alexa.com/data?cli=10&dat=snbamz&url=%s' % (url)).read()

        reach_rank = re.findall("REACH[^\d]*(\d+)", data)
        if reach_rank: reach_rank = reach_rank[0]
        else: reach_rank = -1

        popularity_rank = re.findall("POPULARITY[^\d]*(\d+)", data)
        if popularity_rank: popularity_rank = popularity_rank[0]
        else: popularity_rank = -1

        return int(popularity_rank), int(reach_rank)

    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        return None
 
 

class PluginPagerank(PluginMixin):
    name = unicode(_("Check pagerank"))
    description = unicode(_("Check pagerank"))
    wait_for_download = False
    
    def run(self, command):
        from scanner.models import Results
        domain = command.test.domain()

        rank = get_pagerank(domain)
        
        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)
        res.output_desc = unicode(_("google pagerank") )
        res.output_full = unicode(_("<p>A <a href='http://en.wikipedia.org/wiki/PageRank'>PageRank</a> results from a mathematical algorithm based on the graph, the webgraph, created by all World Wide Web pages as nodes and hyperlinks as edges.</p><p>Your website pagerank is %s.</p>"%(rank ) ))
        
        if ( int(rank) <2):
            res.status = RESULT_STATUS.warning
        else:              
            res.status = RESULT_STATUS.info
        res.save()

        
        (popularity_rank,reach_rank) = get_alexa_rank(domain)           
        res = Results(test=command.test, group = RESULT_GROUP.seo, importance=1)
        res.output_desc = unicode(_("alexa pagerank") )
        res.output_full = unicode(_("<p>Alexa collects statistics about visits by internet users to websites through the Alexa Toolbar. Based on the collected data, Alexa computes site ranking.</p> <p>Ranking for your site:</p> <li>popularity rank: %s</li> <li>reachability rank: %s</li>"%(popularity_rank,reach_rank ) ))
        if (popularity_rank < 0) | (reach_rank < 0):
            res.status = RESULT_STATUS.warning
        else:
            res.status = RESULT_STATUS.info
        res.save()
                    
        return STATUS.success



if __name__ == '__main__':
    main()
