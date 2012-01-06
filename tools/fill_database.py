#!/usr/bin/env python
from django.core.management import setup_environ
import sys

def apath(x):
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__),x))

sys.path.insert(0,apath('../gworker/'))
sys.path.insert(0,apath('../gpanel/'))
sys.path.insert(0,apath('../'))

import gpanel.settings
setup_environ(gpanel.settings)

import sys
import os
import random
from time import sleep
from datetime import datetime
from datetime import timedelta
from scanner.models import (UsersTest,CurrentTest,TariffDef,
                           TESTDEF_PLUGINS,Profile, Domain, 
                           NOTIFY_TYPES, TariffDef_TestDef, Contact,
                            UsersTest_Contact)
from django.db import transaction
from random import choice,randint, sample
from datetime import datetime as dt,timedelta as td
from django.contrib.auth.models import User 



def rlogin():
    return choice(['grzeczna_','maly_','wesoly_','zielony_','czekajaca_','smutny_','tonieja_','kwiat_']) + \
           choice(['tomek','mateusz','damian','ania','kasia','monika','matylda','jeremiasz', 'romek','Bazin'])+\
           str(randint(10,999))
    
def rtarifname():
    return choice(['demo','premium','standard','enterprise'])+str(randint(10,50))
            
def rtestname():
    return "Check" + choice([
            'Certificate',
            'Ping',
            'ErrorCode',
            'Answer',
            'Property',
            'Port',
            'Time',
            'Quality',
            ])          +str(randint(10,50))

def rdomain():
    return choice([
            'www.',
            '',
            ]) + choice([
                'penis',
                'onet',
                'slashdot',
                'osnews',
                'insure',
                'sex',
                'fund',
                'porn',
                'business',
                'diamond',
                'beer',
                'israel',
                'casino',
                'toys',
                'google',
                'gmail',
                'korea',
                'shop',
                'scanner',
                'wp',
                '007',
                'enom'
                ]) + choice([
                    '.com',
                    '.pl',
                    '.eu',
                    '.co.uk',
                    '.org',
                    '.net',
                    '.info',
                    ])


def remail(username="asia"):
    return username + str(randint(10,50)) + choice([
                'gmail.com',
                'wp.pl',
                'poczta.onet.pl',
                ])

def rphone():
    return "%03d-%03d-%03d"%(
                             randint(0,999),
                             randint(0,999),
                             randint(0,999),
    )
                

def add_tariff():
    tests = ['http_code', 'w3c_valid', 'domainexpdate']
    s = TariffDef(price=randint(10,50), 
                  duration=randint(10,50), 
                  name=rtarifname(), 
                  number_of_domains=randint(1,10), 
                  number_of_tests=randint(1,10))
    s.save()
    print 'add tariff %s'%s.name

    #for test in sample(tests,2): #jak bedzie wiecej testow to moze ma to sens
    for test in tests:
        tdef = TariffDef_TestDef(tariff_def=s,
                                 test_def=test,
                                 max_frequency=randint(1,10))
        tdef.save()
        print ' * test in tariff %s'%tdef.test_def
    #s.save()
    return s
    


def add_uuser():
    username=rlogin()
    print 'add user %s'%username
    tarif= random.choice(TariffDef.objects.all())
    u = User(username=username, email=remail(username))
    u.save()
    s = Profile(user=u, expiration_date = '2020-01-01 20:20', tariff_def=tarif )
    s.save()

    #dodajmy kilka kontaktow
    for x in xrange(randint(2,6)):
        _type = choice(NOTIFY_TYPES._choice_dict.values())
        login_add=''
        if _type == NOTIFY_TYPES.email:
            login_add=' poczta'
            _value = remail()
        elif _type == NOTIFY_TYPES.phone:
            login_add=' sms'
            _value = rphone()

        c=Contact(user=u,
                  type=_type,
                  description = rlogin()+login_add,
                  value = _value
                 )
        c.save()
        print ' * add contact %s'%c.description
    return s



with transaction.commit_on_success():
    for x in xrange(randint(1,5)):
        add_tariff()

    for x in xrange(randint(3,10)):
        add_uuser()
    
    users = User.objects.exclude(username='root')
    for user in users:
        print 'for user %s'%user
        
        
        #xx = TariffDef_TestDef.objects.filter(tariff_def=user.get_profile().tariff_def)
        tests = [ (t.test_def,t.max_frequency) for t in  user.get_profile().tariff_def.tests.all() ]
        #tests = [ (t.test_def,t.max_frequency) for t in xx ]

        print 'for test in user tariff'
        for test,max_freq in sample(tests,len(tests)):
            try: #in case of non-exsiting domain...
                domain=Domain(url=rdomain(), user=user )
                domain.clean()
                domain.save()
            except:
                break
            
            td = TariffDef_TestDef.objects.filter(test_def=test)[1]
            ut = UsersTest(user=user,test_def=td,frequency=randint(max_freq,20),domain=domain)
            ut.save()
            ut.users_test_options.port = 80
            ut.save()
            print '   * add userstest %s for %s'%(ut.test_def,ut.domain)


            contacts = Contact.objects.filter(user=user)
            for contact in sample(contacts,len(contacts)):
                c = UsersTest_Contact(contact=contact,
                                      users_test=ut,
                                      sensitivity=randint(1,4)
                                     )
                c.save()
                print '      * add contact %s'%c

