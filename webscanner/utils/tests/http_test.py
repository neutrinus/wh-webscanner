
import pytest
from ..http import extract_domain_from_url, check_domain_name, check_effective_tld, extract_root_domain


valid_one_level_tld_domains = (
    'jogger.pl',
    'debian.org',
    'wp.pl',
    'wykop.pl',
    'slashdot.com',
    'example.org',
    'witaj.cc',
    'some.name',
    'webcheck.me',
)

valid_two_level_tld_domains = (
    'amazon.co.uk',
    'pwr.wroc.pl',
    'sascha.miro-edv.de',
)

valid_multi_level_domains = (
    'witaj.gdzies.pl',
    'oj.oj.oj.pl',
    'wroclaw.wroc.pl',
)

valid_internet_domains = valid_one_level_tld_domains + valid_two_level_tld_domains + valid_multi_level_domains

valid_intranet_domains = (
    'localhost.localdomain',
    'my.own.tld.domain.xxasdd',
    'my.tld_domain_hey',
    'domain.org.org.my_own_tld',
)

valid_local_domains = (
    'localhost',
)

valid_domains = valid_internet_domains + valid_intranet_domains + valid_local_domains

invalid_domains = (
    'http:domain',
    'domain:22',
    'http://domain.pl',
    'http://domain.pl/witaj',
    'http://domain.pl/witaj?ok=1',
    'domain.pl#something',
    'domain.pl?something=1',
)


@pytest.mark.parametrize(('uri', 'domain'),
                         (('http://onet.pl', 'onet.pl'),
                          ('http://wp.pl', 'wp.pl'),
                          ('http://witaj.mikolaju.w.naszym.kraju.com.uk', 'witaj.mikolaju.w.naszym.kraju.com.uk'),
                          ('https://something/with/an?another=something&and=1#egg=Nein', 'something'),
                          ))
def test_extract_domain(uri, domain):
    assert extract_domain_from_url(uri) == domain


@pytest.mark.parametrize('uri',
                         ('wp.pl', 'onet.pl', 'Fail/sadas/a', 'ftp:/ok/jest'))
def test_extract_domain_with_not_proper_uri(uri):
    pytest.raises(ValueError, extract_domain_from_url, uri)


@pytest.mark.parametrize('domain',
                         valid_domains)
def test_check_domain_name(domain):
    assert check_domain_name(domain)


@pytest.mark.parametrize('domain',
                         invalid_domains)
def test_check_domain_name_for_invalid_domains(domain):
    pytest.raises(ValueError, check_domain_name, domain)


@pytest.mark.parametrize('domain',
                         valid_internet_domains)
def test_check_effective_tld(domain):
    assert check_effective_tld(domain)


@pytest.mark.parametrize('domain',
                         invalid_domains + valid_intranet_domains + valid_local_domains)
def test_check_effective_tld_with_invalid_domains(domain):
    pytest.raises(ValueError, check_effective_tld, domain)


@pytest.mark.parametrize('domain',
                         valid_internet_domains + valid_intranet_domains)
def test_check_two_level_tld(domain):
    assert extract_root_domain(domain)


@pytest.mark.parametrize('domain',
                         valid_local_domains + invalid_domains)
def test_check_two_level_tld_with_one_level_domain(domain):
    pytest.raises(ValueError, extract_root_domain, domain)
