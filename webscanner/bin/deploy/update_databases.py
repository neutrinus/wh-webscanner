#!/usr/bin/env python
import os
import sys
sys.path.append('../../../')
sys.path.append('../../')
sys.path.append('../')
sys.path.append('./')


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# THIS IS NOT PROPER WAY TO LOAD DJANGO SETTINGS
# but in this case we want to operate on settings
# before djangi initialize it (django can raise some errors where
# the files are missing, so we want to get these files to make
# django happy)

from django.core.management import setup_environ
import webscanner.settings
setup_environ(webscanner.settings)

import logging
import importlib

import requests

#from webscanner.utils.processes import process_wrapper


def main(args):
    DBS = webscanner.settings.WEBSCANNER_DATABASES
    import argparse
    argparser = argparse.ArgumentParser('Local databases updater')
    argparser.add_argument('-u', '--update',
                           action='store_const',
                           const='update',
                           dest='action',
                           help='Update local databases (by default update only databases which files not exist locally')
    argparser.add_argument('-l', '--list',
                           action='store_const',
                           const='list',
                           dest='action',
                           help='List configured databases and show their statuses (default action)')
    argparser.add_argument('-f', '--force',
                           action='store_true',
                           help='Update also databases which exist locally.')
    argparser.add_argument('-d', '--debug',
                           action='store_true')

    args = argparser.parse_args(args)

    log = logging.getLogger('webscanner.update_databases')
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    log.info('** Updating local databases **')

    def update_db(source, dest_path):
        codec = source.get('codec', None)
        source = source['url']
        if not source.strip():
            log.info('      Error, source is invalid')
        if 'file://' in source:
            source = source[7:]
        if '://' in source:
            log.info('      Updating from url: %s' % source)
            r = requests.get(source)
            if codec == 'gzip':
                log.debug('       - unpacking gzip')
                temp_path = dest_path + '.TEMP_DOWNLOAD'
                with open(temp_path, 'w') as f:
                    f.write(r.content)
                import gzip
                with gzip.open(temp_path) as f, open(dest_path, 'w') as f2:
                    f2.write(f.read())
                os.unlink(temp_path)
            else:
                with open(dest_path, 'w') as f:
                    f.write(r.content)
        else:
            log.info('      Updating from %s by hardlinking' % source)
            if os.path.isfile(source):
                os.link(source, dest_path)
            else:
                raise IOError('Source does not exist.')

    def update_run_python(source, path):
        module_chain, func_name = source['python'].split(':', 1)
        #module_names = module_chain.split('.')
        try:
            module = importlib.import_module(module_chain)
            func = getattr(module, func_name)
        except Exception:
            log.exception('Error while importing module: %s' % source['python'])
            return
        return func

    if args.action == 'update':

        for name, data in DBS.items():
            msg = '%s (path:%s)' % (name, data['path'])
            if os.path.exists(data['path']):
                if args.force:
                    log.info('  [forced] %s' % msg)
                else:
                    log.info('  [  ok  ] %s' % msg)
                    continue
            else:
                log.info('  [update] %s' % msg)

            sources = data['sources']
            for source_ in sources:
                # update from first channel, if it fails get next
                # one
                try:
                    if 'url' in source_:
                        update_db(source_, data['path'])
                    if 'python' in source_:
                        update_run_python(source_, data['path'])(source_, data['path'], data)
                    break
                except Exception as error:
                    if args.debug:
                        log.exception('Cannot update %s' % source_)
                    else:
                        log.error("ERROR: %s" % error)
                    continue
            if not os.path.exists(data['path']):
                log.error('  [error ] %s is not updated!' % name)

        log.info('Exiting...')

    # default action: list
    else:
        for name, data in DBS.items():
            status = ' ok ' if os.path.isfile(data['path']) else 'fail'
            log.info('[%s] %30s - %40s' % (status, name, data['path']))
        return 0


if __name__ == '__main__':
    console = logging.StreamHandler()
    log = logging.getLogger()
    log.addHandler(console)
    log.setLevel(logging.DEBUG)
    log.debug('start script')
    main(sys.argv[1:])
else:
    raise Exception('You should not import this module. It is intendet to run as standalone script only!')
