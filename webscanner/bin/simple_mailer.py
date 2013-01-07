#! /usr/bin/env python
# -*- coding: utf-8 -*-

###
### Configuration is done after imports, please scroll several lines below
###

from django.core.management import setup_environ
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(os.path.join(os.path.dirname(__file__), './'))

import webscanner.settings
setup_environ(webscanner.settings)

# real part of the script
import yaml
import os
import argparse
import logging
import datetime
from django.template import Template, Context
from django.core.mail import EmailMessage, get_connection
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sites.models import Site


CONFIGURATION = {
    'survey': {'description': 'Send users a satisfaction survey',
                'users': lambda: User.objects.filter(date_joined__lte=datetime.date.today()-datetime.timedelta(days=7))),
                'template': os.path.join(settings.PROJECT_PATH, 'emails', 'survey.html'),
                'subject': 'We need your help',  # this will be prefixed like all django emails
                }
}


log = logging.getLogger('webscanner.bin.simple_mailer')


def prepare_keywords(args):
    if not args:
        return {}
    return {x.split('=', 1)[0]: x.split('=', 1)[1] for x in args}


if __name__ == '__main__':
    log.debug('start simple mailer')
    argparser = argparse.ArgumentParser(epilog='''
        To each template you defined there will be passed following keywords arguments:
        user - user instance, datetime - current utc datetime, site - current site (django.contirb.sites)
    ''')
    argparser.add_argument('-n', '--name',
                           help='Use a template with a `name`. It is configured in a top of source code')
    argparser.add_argument('-c', '--context',
                           action='append',
                           help='You can pass additional variables to template. Example `-c "keyword=$(ls)"`. You can use it multiple times')
    argparser.add_argument('command',
                           action='store',
                           choices=['send', 'list'],
                           help='send - send message specified with template (-n), list - print available templates')
    argparser.add_argument('--simulate',
                           action='store_true',
                           default=False,
                           help='Not send emails and do no update cache! Print emails to console instead.')
    args = argparser.parse_args(sys.argv[1:])
    if args.command == 'list':
        for name, conf in CONFIGURATION.iteritems():
            print 'NAME: %-20s DESC: %-s' % (name, conf['description'])
        sys.exit(0)
    elif args.command == 'send':
        if not args.name:
            raise Exception('-n (--name) is required')
        if args.name not in CONFIGURATION:
            raise Exception('template `%s` is not configured. Use `list` to see available templates' % args.name)
        log = logging.getLogger('webscanner.bin.simple_mailer.%s' % args.name)

    config = CONFIGURATION[args.name]

    try:
        global_context = prepare_keywords(args.context)
    except Exception as error:
        log.exception('You have do pass context like -c KEY=VALUE, please correnct.')
        sys.exit(1)

    if not os.path.isfile(config['template']):
        raise IOError('%s does not exist' % config['template'])

    template = Template(open(config['template']).read())
    cache_path = '%s_sent_cache' % config['template']
    if not os.path.isfile(cache_path):
        log.info('Cache for {template} ({cache_path}) not exists.'.format(template=config['template'],
                                                                          cache_path=cache_path))
        cache = {}
    else:
        log.info('Loading cache for {template} from {cache_path}'.format(template=config['template'],
                                                                         cache_path=cache_path))
        # this is very very stupid and simple cache :)
        try:
            cache = yaml.load(open(cache_path).read())
            if not cache:
                cache = {}
            elif not isinstance(cache, dict):
                log.error('Cache has wrong format!!!')
                sys.exit(1)
        except Exception:
            log.exception('Error while loading data from cache. Is it valid yaml?')
            sys.exit(1)
    connection = get_connection()

    users = config['users']()

    log.info('Sending {template} to {users_count} active users.'.format(template=config['template'], users_count=len(users)))
    try:
        for user in users:
            if user.pk in cache:
                log.info('Not sending to {user}. It was sent {date}'.format(user=repr(user), date=cache[user.pk]))
                continue
            log.info('Sending {template} to {user}...'.format(template=config['template'],
                                                              user=repr(user)))
            ctx = dict(global_context)
            ctx.update(dict(
                user=user,
                site=Site.objects.get_current(),
                datetime=datetime.datetime.utcnow()))
            email = EmailMessage(subject='%s %s' % (settings.EMAIL_SUBJECT_PREFIX, config['subject']),
                                 body=template.render(Context(ctx)),
                                 from_email=settings.DEFAULT_FROM_EMAIL,
                                 to=(user.email,),
                                 headers={'Reply-To': settings.DEFAULT_SUPPORT_EMAIL})
            try:
                if args.simulate:
                    print email.message()
                else:
                    email.send()
            except Exception as error:
                log.exception('There was error while sending email to %r' % user)
                continue
            cache[user.pk] = dict(
                pk=user.pk,
                email=user.email,
                timestamp=datetime.datetime.utcnow())
    finally:
        if not args.simulate:
            log.debug('saving cache')
            open(cache_path, 'w').write(yaml.dump(cache, default_flow_style=False))
else:
    raise Exception('You should not import this module. It is intendet to run by cron!')
