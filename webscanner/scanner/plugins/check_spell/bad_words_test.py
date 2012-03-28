
from bad_words import BadWordsDB

from tempfile import tempdir

def apath(s):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),s))

examples = '''
http://onet.pl http://wykop.pl http://google.com http://facebook.com
http://wp.pl http://washingtonpost.com http://thetimes.com http://bbc.com
http://slashdot.com http://kentcommunications.net http://txtpress.de
http://jogger.pl http://autohotkey.com http://moviehawk.org
http://www.acoobe.com http://skeoh.com http://new.hathirtyone.com/
http://alexba.eu http://jobtrends.pl http://profiklima.pl
http://www.bullguard.com http://www.aldamagolf.com http://www.tuxboard.com
http://amazon.com http://baidu.com http://wikipedia.org
http://pl.wikipedia.org http://live.com http://qq.com http://twitter.com
http://linkedin.com http://taobao.com http://msn.com http://ebay.com
http://bin.com http://t.co http://microsoft.com http://apple.com
http://paypal.com http://imdb.com http://pinterest.com http://blogger.com
http://ask.com http://tmall.com http://aol.com http://espn.go.com
http://adobe.com http://conduit.com http://alibaba.com http://livejasmin.com
http://thepiratebay.se http://godaddy.com http://alipay.com http://amazon.de
http://bp.blogspot.com http://stackoverflow.com'''.split()

def test_bad_words_db():

    path = tempdir()

    db = BadWordsDB(path)
