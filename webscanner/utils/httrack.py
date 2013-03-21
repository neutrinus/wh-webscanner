
import os

import sh
import requests
# python-magic
from magic import Magic


def httrack_download_website(url, path, PATH_HTTRACK=None):
    '''url is resolved by requests module (http redirection is not shown to user
    path - must exists, and good if it's empty
    '''
    path = str(path)
    domain = requests.head(url, timeout=5).url

    cmd = [
        # === GENERAL
        '--path', path,  # where to place the files
        # === LIMITS
        '--depth=2',  # depth level
        '--ext-depth=0',  # depth level for external sites
        '-m10485760,2097152',  # max size for non html 10MB, html 2MB
        '--max-time=90',
        '--disable-security-limits',
        '--max-rate=5000000', # in bytes/sec = 5MB/s
        '--connection-per-second=20', # maximum number of connections/seconds
        # === FLOW
        '--sockets=40',  # multiple connections
        # === LINKS
        '--extended-parsing',  # read links not only in clear html (in JS) - this is by default
        '--near',  # get non html files
        #'--test', # test all URLs (even forbidden ones)
        # === BUILD
        # 0 - original structure
        # 1 - html in web, images in images
        # 99 - random names in web
        # 1099 - random names (no web dir)
        #'--structure=0',  # structure: 0-original, 1+ ??
        #'-or', '-N "%h%p/%n%q.%t'  # own structure?
        '--structure=99',

        '--keep-links=4',  # keep original links
        # it seams --replace-external does not much
        #'--replace-external',  # replace external links with errors, may be good, TEST WHETHER THIS NOT REMOVE THIS LINKS
        '--include-query-string',  # TEST: where this add this?
        '--generate-errors=0',  # TEST: I think errors we can read from log
        # === SPIDER
        '--robots=0',  # not follow robots.txt
        '--keep-alive',
        # === BROWSER ID
        '--user-agent=',  # empty is ok, sometimes when passen unknown, servers serve mobile site
        '--referer=http://webcheck.me',
        '--footer=',  # do not add anything to files
        # === LOG, INDEX, CACHE - probably we do not need logs (only new.txt in hts-cache
        #'--extra-log',
        #'--debug-log',  # TEST what is there
        #'--file-log',  # log in files?
        #'--single-log',  # one log
        '-I0',  # '--index=0' - this does not work,  # do not make an index
        # === EXPERT
        #'--debug-headers',  # TEST: do we need this? - not very useful
        # === GURU
        #'--debug-xfrstats',  # generate ops log every minute - not very useful
        #'--debug-ratestats',  # generate rate stats - not very useful

        domain,  # site to scan
        '+*',  # which files to get
    ]

    if not PATH_HTTRACK:
        httrack = sh.httrack
    else:
        httrack = sh.__getattr__(PATH_HTTRACK)

    httrack(*cmd)


def parse_new_txt(file_path, root_path=None):
    file_type = Magic(mime=True)
    f = open(file_path)
    next(f)  # omit first line
    for line in f:
        data = line.strip().split('\t')
        sizes = data[1].split('/')
        try:
            exists = os.path.exists(data[8])
            size = os.path.getsize(data[8])
            type = file_type.from_file(data[8])
        except (IOError, OSError):
            exists = False
            size = 0
            type = ''
        yield {'download_date': data[0],
               'remote_size': int(sizes[0]),  # httrack remote size
               'local_size': int(sizes[1]),  # httrack local size
               'flags': data[2],
               'http_status_code': data[3],
               'status': data[4],
               'httrack_mime': data[5],  # httrack mime type
               'etag': data[6],
               'url': data[7],
               'path': os.path.relpath(data[8], root_path) if root_path else data[8],
               'from_url': data[9],
               'mime': type,
               'size': size,
               'exists': exists}
