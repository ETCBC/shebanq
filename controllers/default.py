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
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

# long import statement for editor and web2py
# from applications.shebanq.modules import clamdros
# short import statement only satisfies web2py
#import trypy as tpy

#only use this during development:
# reload(clamdros)

import json

def index():
    """
    example action using the internationalization operator T 
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    response.title = T("SHEBANQ")
    response.subtitle = T("Query the Hebrew Bible through the ETCBC4 database")
    return dict()

def about():
    response.title = T("SHEBANQ")
    response.subtitle = T("About the ETCBC4 database")
    return dict()

def help():
    response.title = T("SHEBANQ")
    response.subtitle = T("Help for using SHEBANQ")
    return dict()

def save_dataview():
    response.cookies['dataview'] = request.vars.dataviewvars
    response.cookies['dataview']['expires'] = 30 * 24 * 3600
    response.cookies['dataview']['path'] = '/'
    return ''

def save_queryview():
    response.cookies['queryview'] = request.vars.queryviewvars
    response.cookies['queryview']['expires'] = 30 * 24 * 3600
    response.cookies['queryview']['path'] = '/'
    return ''

def save_querymap():
    doremove = request.vars.remove 
    if doremove == 'all':
        new_map_json = json.dumps({})
    else:
        new_map = json.loads(request.vars.querymapvars)
        old_map = {}
        if request.cookies.has_key('querymap'):
            old_map = json.loads(request.cookies['querymap'].value)
        old_map.update(new_map)
        if doremove and doremove in old_map:
            del old_map[doremove]
        new_map_json = json.dumps(old_map)
    response.cookies['querymap'] = new_map_json
    response.cookies['querymap']['expires'] = 30 * 24 * 3600
    response.cookies['querymap']['path'] = '/'
    return new_map_json

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """

    response.title = T("User Profile")
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())


