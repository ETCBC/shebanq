#!/usr/bin/env python
#-*- coding:utf-8 -*-

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

# # Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
if 0:
    from . import *
    # End of fake imports to satisfy the editor.
    #

import os
import tempfile
from contextlib import contextmanager

@contextmanager
def make_temp_file():
    """
    Yields a temporary file as file descriptor and path.
    yields temp = fd, temp_path

    """
    temp = tempfile.mkstemp(prefix='shebanq',suffix='.mql',text=True)
    try:
        yield temp
    finally:
        os.remove(temp[1])


def index():
    redirect(URL('edit_query'))


def get_record_id():
    # web2py returns hidden id and (if present) id in URL, so id can be None, str or list(str)
    record_id = request.vars.id
    if request.vars.id is not None:
        if type(request.vars.id) == list:
            record_id = int(request.vars.id[0])
        elif request.vars.id.isdigit():
            record_id = int(request.vars.id)
        else:
            raise HTTP(404, "Object not found in database: " + str(record_id))
    return record_id


@auth.requires_login()
def check_query_access_write(record_id=get_record_id()):
    authorized = True

    if record_id is not None and record_id > 0:
        mql_record = db.mql_queries[record_id]
        if mql_record is None:
            raise HTTP(404, "Object not found in database.")
        if mql_record.created_by != auth.user.id:
            authorized = False

    return authorized


@auth.requires_login()
def check_query_access_execute(record_id=get_record_id()):
    authorized = False

    if record_id is not None:
        mql_record = db.mql_queries[record_id]
        if mql_record is None:
            raise HTTP(404, "Object not found in database.")
        if mql_record.created_by == auth.user.id:
            authorized = True

    return authorized


def get_mql_form(mql_record, readonly=False):
    mql_form = SQLFORM(db.mql_queries, record=mql_record, readonly=readonly,
       showid=True, ignore_rw=False,
       labels={'mql': 'MQL Query', 'handler_name': 'Context '},
       col3={
           'name': 'A name for this query that will be shown in list views.',
           'description': 'A description and motivation for this query.',
           'mql': A('MQL Query Guide (pdf)',
                    _target='_blank',
                    _href='http://emdros.org/MQL-Query-Guide.pdf'),
           'handler_name': 'What context renderer should be used for displaying the result.',
           'context_level': 'Display embedded blocks, starting with block at \'Context Level\'. '
                            + 'The first block in the hierarchy has level 0.',
           'context_marker': 'Display blocks marked with the \'Context Marker\' keyword. '
                             + 'In the query marks start with a back quote (`) and are followed by the keyword.',
       },
       formstyle='divs',
       buttons=[TAG.button('Save', _type='submit', _name='button_save'),
                TAG.button('Execute', _type='submit', _name='button_execute'),
                TAG.button('New', _type='submit', _name='button_new'), ]
    )
    return mql_form


def handle_response(mql_form):
    mql_form.process(keepvalues=True)
    if mql_form.accepted:
        record_id = str(mql_form.vars.id)

        if request.vars.has_key('button_save'):
            session.flash = 'saved query as ' + record_id

        elif request.vars.has_key('button_execute'):
            session.flash = 'executing query ' + record_id
            redirect(URL('execute_query', vars=dict(id=record_id)))

        elif request.vars.has_key('button_new'):
            session.flash = 'saved previous query as ' + record_id
            record_id = '0'

        redirect(URL('edit_query', vars=dict(id=record_id)))

    elif mql_form.errors:
        response.flash = 'form has errors, see details'


@auth.requires(lambda: check_query_access_write())
def edit_query():

    mql_record = get_record_id()
    if mql_record is None:
        mql_record = db(db.mql_queries.created_by==auth.user).select().last() or 0

    mql_form = get_mql_form(mql_record)
    handle_response(mql_form)
    return dict(form=mql_form, message=T('Edit Query'))


@auth.requires(lambda: check_query_access_execute())
def execute_query():
    # long import statement for editor and web2py
    from applications.shebanq.modules import clamdros

    record_id = get_record_id()
    mql_form = get_mql_form(record_id)
    handle_response(mql_form)

    mql_record = db.mql_queries[record_id]
    client = clamdros.Client()

    with make_temp_file() as temp:
         mql_file = os.fdopen(temp[0], 'w')
         mql_file.write(mql_record.mql)
         mql_file.close()
         r_files, r_context = client.query(temp[1],
                         contexthandlername=mql_record.handler_name,
                         contextlevel=mql_record.context_level,
                         contextmark=mql_record.context_marker)

    client.remove()

    print(len(r_files))

    return dict(form=mql_form, message=T('Execute Query'))#, r_files=r_files, r_context=r_context)


@auth.requires_login()
def my_queries():
    grid = SQLFORM.grid(db.mql_queries.created_by==auth.user,
        fields={db.mql_queries.id, db.mql_queries.name, db.mql_queries.created_on,
                db.mql_queries.modified_on, db.mql_queries.modified_by},
        orderby=~db.mql_queries.modified_on,
        selectable = lambda ids : redirect(URL('linquer', 'delete_multiple', vars=dict(id=ids))),
        editable=False,
        details=False,
        create=False,
        links = [lambda row: A(SPAN(_class='icon pen icon-pencil'),
                               SPAN('Edit', _class='buttontext button', _title='Edit'),
                               _class='button btn',
                               _href=URL('linquer','edit_query',vars=dict(id=row.id)),),],
        paginate=3,
        csv=False)
    return locals()


@auth.requires_login()
def delete_multiple():
    print request.vars.id
    session.flash="deleted " + str(request.vars.id)
    redirect(URL('my_queries'))