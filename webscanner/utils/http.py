#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
from urlparse import urlparse
from django.conf import settings


log = logging.getLogger(__name__)


log.info('Loading "EFFECTIVE_TLDS" database from "%s".' % settings.WEBSCANNER_DATABASES['EFFECTIVE_TLDS']['path'])
EFFECTIVE_TLDS_CACHE = [line.strip() for line in open(settings.WEBSCANNER_DATABASES['EFFECTIVE_TLDS']['path'])
                        if line.strip() and not line.strip().startswith('//')]


log.info('Loading "TWO_LEVEL_TLDS" database from "%s".' % settings.WEBSCANNER_DATABASES['TWO_LEVEL_TLDS']['path'])
TWO_LEVEL_TLDS_CACHE = [line.strip() for line in open(settings.WEBSCANNER_DATABASES['TWO_LEVEL_TLDS']['path']) if line.strip()]


def extract_domain_from_url(url):
    url = urlparse(url)
    if not url.scheme:
        raise ValueError('Scheme/protocol element for url is missing, domain cannot be correctly parsed.')
    if not url.netloc:
        raise ValueError('Domain cannot be correctly parsed. There are some errors in URI.')
    return url.netloc


def check_domain_name(domain):
    if '/' in domain:
        raise ValueError('Domain cannot contains "/" (probably query path is added).')
    if ':' in domain:
        raise ValueError('Domain cannot contains ":" (probably protocol or port is added).')
    if '?' in domain:
        raise ValueError('Domain cannot contains "?" (probably querystring is added).')
    if set(('#',)).intersection(domain):
        raise ValueError('Domain cannot contains not allowed characters.')
    return True


def check_effective_tld(domain):
    """
    returns domain one dot before TLDs

    :param domain: only domain without query, port or protocol

    http://stackoverflow.com/questions/1066933/how-to-extract-domain-name-from-url/1069780#1069780
    """
    check_domain_name(domain)
    urlElements = domain.split('.')

    #print urlElements
    # urlElements = ["abcde","co","uk"]

    for i in range(-len(urlElements), 0):
        lastIElements = urlElements[i:]
        #    i=-3: ["abcde","co","uk"]
        #    i=-2: ["co","uk"]
        #    i=-1: ["uk"] etc

        candidate = ".".join(lastIElements)  # abcde.co.uk, co.uk, uk
        wildcardCandidate = ".".join(["*"] + lastIElements[1:])  # *.co.uk, *.uk, *
        exceptionCandidate = "!" + candidate

        # match tlds:
        if (str(exceptionCandidate) in EFFECTIVE_TLDS_CACHE):
            return ".".join(urlElements[i:])
        if (str(candidate) in EFFECTIVE_TLDS_CACHE or str(wildcardCandidate) in EFFECTIVE_TLDS_CACHE):
            return ".".join(urlElements[i - 1:])
            # returns "abcde.co.uk"
    raise ValueError("Domain not in global list of TLDs")


def extract_root_domain(domain):
    # Takes the location of the file listing the known TLDs where second level registration is well-known
    # An example of such a file can be downloaded from:
    # http://spamcheck.freeapp.net/two-level-tlds
    check_domain_name(domain)
    dnsParts = domain.split('.')
    if len(dnsParts) < 2:
        raise ValueError('Cannot check one level domain name.')
    secondLevelTld = dnsParts[-2] + '.' + dnsParts[-1] + "\n"
    if (secondLevelTld in TWO_LEVEL_TLDS_CACHE) and len(dnsParts) > 2:
        registeredName = dnsParts[-3] + '.' + dnsParts[-2] + '.' + dnsParts[-1]
    else:
        registeredName = dnsParts[-2] + '.' + dnsParts[-1]
    return registeredName
