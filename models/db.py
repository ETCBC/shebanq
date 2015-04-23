#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 DANS-KNAW
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# #######################################################################
# Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
if 0:
    from . import *
# End of fake imports to satisfy the editor.
# #######################################################################

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
#request.requires_https()

from get_db_config import config

dc_u = config['shebanq_user']
dc_p = config['shebanq_passwd']
dc_h = config['shebanq_host']

version_order = '''4 4b 4s'''.split()

versions = {
    '4': {
        'name': 'etcbc4',
        'date': '2014-07-14',
        'desc': 'First version of the ETCBC4 database in SHEBANQ',
        'notes': 'The data for this version is a snapshot. At some locations the encoding is not yet finished. We needed a reasonable version then because of the deadline for SHEBANQ as a project.',
    },
    '4b': {
        'name': 'etcbc4b',
        'date': '2015-04-09',
        'desc': 'Current version of the ETCBC4 database, somehwere between versions 4 and 4s',
        'notes': 'This version is updated periodically until version 4s is available; it can be used as a preview to version 4s',
    },
    '4s': {
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

#db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])

# if not request.env.web2py_runtime_gae:
#     ## if NOT running on Google App Engine use SQLite or other DB
#     #db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
#     db = DAL('mysql://shebanquser:shebanqpass@localhost/shebanq', pool_size=1,check_reserved=['all'])
# else:
#     ## connect to Google BigTable (optional 'google:datastore://namespace')
#     db = DAL('google:datastore')
#     ## store sessions and tickets there
#session.connect(request, response, db=db)
#     ## or store session in Memcache, Redis, etc.
#     ## from gluon.contrib.memdb import MEMDB
#     ## from google.appengine.api.memcache import Client
#     ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, secure=False) # secure=True should enforce https for auth
# DR: if we say secure=True, all pages will go over https, currently undesirable, because the homepage should not go over https
# as long as we have a self-signed certificate: users will get a warning!
# instead, we say request.requires_https() whereever needed.
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
# username=False --> use email address
# signature=False --> Where is the API? I *believe* signature=True will enable record versioning.
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'mailrelay.knaw.nl' #'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'foo.bar@dans.knaw.nl'
mail.settings.login = None #'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = False
#If the user tried to access the register page but is already logged in, redirect to profile.
auth.settings.logged_url = URL('user', args='profile')

## if crud is to be used...
# crud.settings.auth = auth
##

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

auth.messages.logged_in = None
auth.messages.logged_out = None

