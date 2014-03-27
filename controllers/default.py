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
from StdSuites.AppleScript_Suite import cubic_centimeters

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

    form=FORM(TEXTAREA(_name='mql_query', requires=[IS_NOT_EMPTY(error_message='please enter a query'), ], _class='query'),
              DIV(
                  DIV(INPUT(_type='radio', _id='handlertype1', _name='handlertype', _value='level', value='level', _class='left_'),
                      LABEL(T('Level'), _for='handlertype1', _class='radio'),
                      INPUT(_type='text', _name='contextlevel', requires=[IS_INT_IN_RANGE(0,)], _value=0),
                      _class='left_'
                  ),
                  DIV(INPUT(_type='radio', _id='handlertype2', _name='handlertype', _value='marks', value='level', _class='left_'),
                      LABEL(T('Marks'), _for='handlertype2', _class='radio'),
                      INPUT(_type='text', _name='contextkey', _value='context'),
                      _class='right_'
                  )
              ),
              INPUT(_type='submit', _value='Execute query'))
    form.add_button('Cancel', URL('index'))

    dictio = dict(form=form, result_context="", result_files=[])

    if form.process(keepvalues=True).accepted:
        print("accepted")
        current_query = form.vars.mql_query
        handler_type = form.vars.handlertype
        contextlevel = form.vars.contextlevel
        contextkey = form.vars.contextkey
        print(handler_type)
        print(contextlevel)
        print(contextkey)
        #check query
        prefix = 'SELECT ALL OBJECTS'
        if current_query[:len(prefix)].lower() != prefix.lower():
            current_query = 'SELECT ALL OBJECTS\nWHERE\n' + current_query

        input_file = "/tmp/mqfile.mql"
        mqfile = open(input_file, "w")
        mqfile.writelines(current_query)
        mqfile.close()

        client = clamdros.Client()
        output = client.query(input_file,
                              contexthandlername=handler_type, contextlevel=contextlevel, contextmark=contextkey)

        dictio["result_context"] = output[1]
        dictio["result_files"] = output[0]

        client.remove()
    elif form.errors:
        response.flash = 'form has errors, see details'

    return dictio


# old result was on separate page..
def result():

    input_file = "/tmp/mqfile.mql"
    mqfile = open(input_file, "w")
    mqfile.writelines(session.mql_query)
    mqfile.close()
    #client = clamdros.Client()
    #output = client.query(input_file)

    return dict(output="old output", result_context="old result context")#output[0], result_context=output[1])


def testform():
    form=FORM(TEXTAREA(_name='mql_query', requires=IS_NOT_EMPTY(), _class='query'),
              INPUT(_type='submit'))
    form['_style']='border:1px solid red'

    print 'test form'

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


####
# def create_self_signed_cert(cert_dir):
#     """
#     create a new self-signed cert and key and write them to disk
#     """
#     from OpenSSL import crypto, SSL
#     from socket import gethostname
#     from pprint import pprint
#     from time import gmtime, mktime
#     from os.path import exists, join
#
#     CERT_FILE = "ssl_certificate.crt"
#     KEY_FILE = "ssl_self_signed.key"
#     ssl_created = False
#     if not exists(join(cert_dir, CERT_FILE)) \
#     or not exists(join(cert_dir, KEY_FILE)):
#     ssl_created = True
#     # create a key pair
#     k = crypto.PKey()
#     k.generate_key(crypto.TYPE_RSA, 4096)
#
#     # create a self-signed cert
#     cert = crypto.X509()
#     cert.get_subject().C = "AQ"
#     cert.get_subject().ST = "State"
#     cert.get_subject().L = "City"
#     cert.get_subject().O = "Company"
#     cert.get_subject().OU = "Organization"
#     cert.get_subject().CN = gethostname()
#     cert.set_serial_number(1000)
#     cert.gmtime_adj_notBefore(0)
#     cert.gmtime_adj_notAfter(10*365*24*60*60)
#     cert.set_issuer(cert.get_subject())
#     cert.set_pubkey(k)
#     cert.sign(k, 'sha1')
#
#     open(join(cert_dir, CERT_FILE), "wt").write(
#     crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
#     open(join(cert_dir, KEY_FILE), "wt").write(
#     crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
#
#     create_self_signed_cert('.')
#     return(ssl_created, cert_dir, CERT_FILE, KEY_FILE)
#
# def generate_ssl_key():
#     ssl_created, cert_dir, CERT_FILE, KEY_FILE = create_self_signed_cert(request.folder + "private/")
#     return(dict(ssl_created=ssl_created, cert_dir=cert_dir, CERT_FILE=CERT_FILE, KEY_FILE=KEY_FILE))
