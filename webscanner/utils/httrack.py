
import os


def parse_new_txt(file_path, root_path=None):
    f = open(file_path)
    next(f)  # omit first line
    for line in f:
        data = line.strip().split('\t')
        sizes = data[1].split('/')
        yield {'download_date': data[0],
               'remote_size': int(sizes[0]),
               'local_size': int(sizes[1]),
               'flags': data[2],
               'http_status_code': data[3],
               'status': data[4],
               'mime': data[5],
               'etag': data[6],
               'url': data[7],
               'path': os.path.relpath(data[8], root_path) if root_path else data[8],
               'from_url': data[9]}
