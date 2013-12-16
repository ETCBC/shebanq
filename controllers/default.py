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
from applications.shebanq.modules import clamdros
# short import statement only satisfies web2py
#import trypy as tpy

#only use this during development:
reload(clamdros)


def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    #response.title = "SHEBANQ"
    #response.subtitle = T("Queries As Annotations")
    #response.flash = T("Welcome to SHEBANQ")
    return dict()


def query():
    # form = SQLFORM.factory(Field('mql_query',
    #                              label='MQL query',
    #                              requires=IS_NOT_EMPTY(),
    #                              type="text"))

    form=FORM(TEXTAREA(_name='mql_query', requires=[IS_NOT_EMPTY(), ], _class='query'),
              INPUT(_type='submit'))

    dictio = dict(form=form, result_context="", result_files=[])

    if form.process(keepvalues=True).accepted:
        print("accepted")
        current_query = form.vars.mql_query
        input_file = "/tmp/mqfile.mql"
        mqfile = open(input_file, "w")
        mqfile.writelines(current_query)
        mqfile.close()
        client = clamdros.Client()
        output = client.query(input_file)

        dictio["result_context"] = output[1]
        dictio["result_files"] = output[0]

        client.remove()

    return dictio


def result():

    input_file = "/tmp/mqfile.mql"
    mqfile = open(input_file, "w")
    mqfile.writelines(session.mql_query)
    mqfile.close()
    client = clamdros.Client()
    output = client.query(input_file)

    return dict(output=output[0], result_context=output[1])


def testform():
    form=FORM(TEXTAREA(_name='mql_query', requires=IS_NOT_EMPTY(), _class='query'),
              INPUT(_type='submit'))

    if form.process(keepvalues=True).accepted:
        print("accepted")
        session.mql_query = form.vars.mql_query

    return dict(form=form)


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
