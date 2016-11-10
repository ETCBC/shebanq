#!/usr/bin/env python
# -*- coding: utf-8 -*-

request.requires_https()

from get_db_config import config

dc_u = config['shebanq_user']
dc_p = config['shebanq_passwd']
dc_h = config['shebanq_host']

version_order = '''4 4b'''.split()

versions = {
    '4': {
        'name': 'etcbc4',
        'date': '2014-07-14',
        'desc': 'First version of the ETCBC4 database in SHEBANQ',
        'notes': 'The data for this version is a snapshot. At some locations the encoding is not yet finished. We needed a reasonable version then because of the deadline for SHEBANQ as a project. The underlying data has been archived at DANS.',
    },
    '4b': {
        'name': 'etcbc4b',
        'date': '2015-11-03',
        'desc': 'Current version of the ETCBC4 database',
        'notes': 'The data for this version is a snapshot. The encoding has been finished, but some checks are still in progress. We needed a reasonable version because more projects are using this data, and some of them report at the SBL annual meeting in November 2015. The underlying data has been archived at DANS.',
    },
    '4s': { # not used
        'name': 'etcbc4s',
        'date': '',
        'desc': 'Stable version of the ETCBC4 database',
        'notes': 'This version corresponds to an officially released version of the ETCBC data.',
    },
}

db = DAL('mysql://{}:{}@{}/{}'.format(
        config['shebanq_user'],
        config['shebanq_passwd'],
        config['shebanq_host'],
        'shebanq_web',
    ),
    migrate_enabled=False, # if session table already exists
    #migrate=False, # if session table does not yet exist
)

passage_dbs = {}

note_db = DAL('mysql://{}:{}@{}/{}'.format(
        config['shebanq_user'],
        config['shebanq_passwd'],
        config['shebanq_host'],
        'shebanq_note',
    ),
    migrate_enabled=False, # if session table already exists
    #migrate=False, # if session table does not yet exist
)

for vr in versions:
    if not versions[vr]['date']: continue
    passage_dbs[vr] = DAL('mysql://{}:{}@{}/{}'.format(dc_u, dc_p, dc_h, 'shebanq_passage{}'.format(vr)), migrate_enabled=False)

# Indeed, we store sessions in the database:
session.connect(request, response, db=db)
response.generic_patterns = ['*'] if request.is_local else []

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, secure=True) # secure=True should enforce https for auth
crud, service, plugins = Crud(db), Service(), PluginManager()
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'localhost' #'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'shebanq@ancient-data.org'
mail.settings.login = None #'username:password'
mail.settings.tls = None

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = False
#If the user tried to access the register page but is already logged in, redirect to profile.
auth.settings.logged_url = URL('user', args='profile')

from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

auth.messages.logged_in = None
auth.messages.logged_out = None

