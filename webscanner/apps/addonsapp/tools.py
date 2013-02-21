
def strip_html_tags(root):
    """
    Take a body text and return only text (without tags)
    """
    for s in root.childGenerator():
        if hasattr(s, 'name'):    # then it's a tag
            if s.name == 'script' or s.name == 'style':  # skip it!
                continue
            for x in strip_html_tags(s): yield x
        else:                     # it's a string!
            yield s
