
import re

# pip: beautifulsoup4
import bs4

__all__ = ['clean_html']


def visible(element):
    '''Required for cleaning html'''
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', element):
        return False
    elif re.match(r'\s*\d+\s*', element):
        return False
    elif not bool(element.strip()) or re.match(r'\s+', element):
        return False
    return True


def clean_html(text, join_result=True):
    '''
    :param text: text can be unicode, string or BeautifulSoup (PageElement)
    :returns: list of strings or string (if you set `join_result=True`)
    '''
    if isinstance(text, (str, unicode)):
        text = bs4.BeautifulSoup(text)
        try:
            text = text.html.body
        except AttributeError:
            pass
    elif isinstance(text, bs4.PageElement):
        pass
    else:
        raise TypeError('`text` has to be str,unicode or bs4.PageElement')

    if text:
        text = filter(visible, text.findAll(text=True))
    else:
        text = []
    if join_result:
        return '\n'.join(text)
    return text
