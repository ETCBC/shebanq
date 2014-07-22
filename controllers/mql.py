#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright 2014 DANS-KNAW
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

# # Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
from shemdros.client.api import CashedMonadsetIterator

if 0:
    from . import *
    # End of fake imports to satisfy the editor.
    #


def get_record_id():
    #print "get_record_id"
    # web2py returns hidden id and (if present) id in URL, so id can be None, str or list(str)
    record_id = request.vars.id
    if request.vars.id is not None:
        if type(request.vars.id) == list:
            record_id = int(request.vars.id[0])
        elif request.vars.id.isdigit():
            record_id = int(request.vars.id)
        else:
            raise HTTP(404, "get_record_id: Object not found in database: " + str(record_id))
    return record_id


@auth.requires_login()
def check_query_access_write(record_id=get_record_id()):
    #print "check_query_access_write"
    authorized = True

    if record_id is not None and record_id > 0:
        mql_record = db.queries[record_id]
        if mql_record is None:
            raise HTTP(404, "No write access. Object not found in database. record_id=" + str(record_id))
        if mql_record.created_by != auth.user.id:
            authorized = False

    return authorized


@auth.requires_login()
def check_query_access_execute(record_id=get_record_id()):
    authorized = False

    if record_id is not None:
        mql_record = db.queries[record_id]
        if mql_record is None:
            raise HTTP(404, "No execute access. Object not found in database. record_id=" + str(record_id))
        if mql_record.created_by == auth.user.id:
            authorized = True

    return authorized


def get_mql_form(mql_record, readonly=False):
    mql_form = SQLFORM(db.queries, record=mql_record, readonly=readonly,
                       showid=False, ignore_rw=False,
                       labels={'mql': 'MQL Query'},
                       col3={'name': 'A name for this query that will be shown in list views.',
                             'description': 'A description and motivation for this query.',
                             'mql': A('MQL quick reference guide (pdf)',
                                      _target='_blank',
                                      _href=URL('static', 'docs/MQL-QuickRef.pdf')),
                             },
                       formstyle='divs',
                       buttons=[TAG.button('Save', _type='submit', _name='button_save'),
                                TAG.button('Execute', _type='submit', _name='button_execute'),
                                TAG.button('Render', _type='submit', _name='button_render'),
                                TAG.button('New', _type='submit', _name='button_new'), ]
                       )
    return mql_form


def handle_response(mql_form):
    #print "handle_response"
    mql_form.process(keepvalues=True)
    if mql_form.accepted:
        record_id = str(mql_form.vars.id)

        if 'button_save' in request.vars:
            session.flash = 'saved query ' + str(mql_form.vars.name)

        elif 'button_execute' in request.vars:
            redirect(URL('execute_query', vars=dict(id=record_id)))

        elif 'button_render' in request.vars:
            redirect(URL('render_query', vars=dict(id=record_id)))

        elif 'button_new' in request.vars:
            session.flash = 'saved previous query ' + str(mql_form.vars.name)
            record_id = '0'

        redirect(URL('edit_query', vars=dict(id=record_id)))

    elif mql_form.errors:
        response.flash = 'form has errors, see details'


def store_monad_sets(record_id, monad_sets):
    db.executesql('DELETE FROM monadsets WHERE query_id=' + str(record_id) + ';')
    #db.monadsets.delete(record_id)
    for monad_set in monad_sets:
        db.monadsets.insert(query_id=record_id, first_m=monad_set[0], last_m=monad_set[1])


def index():
    redirect(URL('edit_query'))


@auth.requires(lambda: check_query_access_write())
def edit_query():
    #print "edit_query"
    mql_record = get_record_id()
    if mql_record is None:
        mql_record = db(db.queries.created_by == auth.user).select().last() or 0

    mql_form = get_mql_form(mql_record)
    handle_response(mql_form)

    return dict(form=mql_form)


@auth.requires(lambda: check_query_access_execute())
def execute_query():
    #print "execute_query"
    from shemdros.client.api import MqlResource
    from shemdros.client.api import RemoteException

    record_id = get_record_id()
    mql_form = get_mql_form(record_id)
    handle_response(mql_form)

    mql_record = db.queries[record_id]
    mql = MqlResource()
    try:
        monad_sets = mql.list_monad_set(mql_record.mql)
        store_monad_sets(record_id, monad_sets)
    except RemoteException, e:
        response.flash = 'Exception while executing query: '
        return dict(form=mql_form, exception=CODE(e.message), exception_message=CODE(parse_exception(e.response.text)))

    response.flash = 'Query executed'
    return dict(form=mql_form, monad_sets=monad_sets, exception=None)


@auth.requires(lambda: check_query_access_execute())
def render_query():
    from shemdros.client.api import RemoteException
    from shebanq_db.etcbc import VerseIterator

    record_id = get_record_id()
    mql_form = get_mql_form(record_id)
    handle_response(mql_form)

    mql_record = db.queries[record_id]
    query = mql_record.mql
    try:
        ms_iter = CashedMonadsetIterator(query)
        store_monad_sets(record_id, ms_iter.monadsets)
        verse_iter = VerseIterator(ms_iter, max_verses=10)

    except RemoteException, e:
        response.flash = 'Exception while executing query: '
        return dict(form=mql_form, exception=CODE(e.message), exception_message=CODE(parse_exception(e.response.text)))

    response.flash = 'Query executed'
    return dict(form=mql_form, exception=None, verse_iter=verse_iter)


def parse_exception(message):
    import xml.etree.ElementTree as ET
    try:
        root = ET.XML(message)
        result = root.find('.//http-status/code').text
        result += ' '
        result += root.find('.//http-status/reason').text
        result += root.find('.//exception/message').text
        return result
    except:
        return "<Unparsable result>"


@auth.requires_login()
def my_queries():
    grid = SQLFORM.grid(db.queries.created_by == auth.user,
                        fields={db.queries.id, db.queries.name, db.queries.created_on,
                                db.queries.modified_on, db.queries.modified_by},
                        orderby=~db.queries.modified_on,
                        selectable=[('Delete selected', lambda ids: redirect(URL('mql', 'delete_multiple', vars=dict(id=ids))))],
                        editable=False,
                        details=False,
                        create=False,
                        links=[lambda row: A(SPAN(_class='icon pen icon-pencil'),
                                             SPAN('Edit', _class='buttontext button', _title='Edit'),
                                             _class='button btn',
                                             _href=URL('mql', 'edit_query', vars=dict(id=row.id)), ), ],
                        paginate=3,
                        csv=False)

    grid[1].element(_type="submit", _value="Delete selected")["_onclick"] = "return confirm('Delete selected records?');"
    return locals()


@auth.requires_login()
def delete_multiple():
    #print request.vars.id
    if request.vars.id is not None:
        for id in request.vars.id:
            db(db.queries.id == id).delete()

    session.flash = "deleted " + str(request.vars.id)
    redirect(URL('my_queries'))
