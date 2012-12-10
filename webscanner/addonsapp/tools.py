#! /usr/bin/env python
# -*- encoding: utf-8 -*-
from urlparse import urlparse
from settings   import apath

PATH_TLD_NAMES = "addonsapp/effective_tld_names.dat.txt"

def extract_domain(url):
    """
    returns domain one dot before TLDs
    """

    #http://stackoverflow.com/questions/1066933/how-to-extract-domain-name-from-url/1069780#1069780

    tlds = []

    try:
        # load tlds, ignore comments and empty lines:
        #https://mxr.mozilla.org/mozilla/source/netwerk/dns/src/effective_tld_names.dat?raw=1
        with open(apath(PATH_TLD_NAMES)) as tldFile:
            tlds = [line.strip() for line in tldFile if line[0] not in "/\n"]
    except IOError:
        raise ValueError("Could not find file %s" % PATH_TLD_NAMES)

    urlElements = urlparse(url)[1].split('.')

    #print urlElements
    # urlElements = ["abcde","co","uk"]

    for i in range(-len(urlElements),0):
        lastIElements = urlElements[i:]
        #    i=-3: ["abcde","co","uk"]
        #    i=-2: ["co","uk"]
        #    i=-1: ["uk"] etc

        candidate = ".".join(lastIElements) # abcde.co.uk, co.uk, uk
        wildcardCandidate = ".".join(["*"]+lastIElements[1:]) # *.co.uk, *.uk, *
        exceptionCandidate = "!"+candidate

        # match tlds:
        if (str(exceptionCandidate) in tlds):
            return ".".join(urlElements[i:])
        if (str(candidate) in tlds or str(wildcardCandidate) in tlds):
            return ".".join(urlElements[i-1:])
            # returns "abcde.co.uk"
    raise ValueError("Domain not in global list of TLDs")

