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

def index():
    redirect(URL('query'))


@auth.requires_login()
def check_query_access():

    print type(request.vars.id), request.vars.id

    if request.vars.id is not None:
        record_id = None
        # web2py returns for parameter id: None, str or list(str)
        if type(request.vars.id) == list:
            record_id = int(request.vars.id[0])

        elif request.vars.id.isdigit():
            record_id = int(request.vars.id)

        if record_id is not None and record_id > 0:
            mql_record = db.mql_queries[record_id]
            if mql_record is None:
                raise HTTP(404, "Object not found in database.")
            if mql_record.created_by != auth.user.id:
                return False


##
    # mql_record = request.vars.id
    #
    # if request.vars.id is not None:
    #     if request.vars.id.isdigit():
    #         mql_record = int(request.vars.id)
    #         if mql_record == 0:
    #             response.flash = 'new query'
    #         # else existing record. user has the right to see requested record?
    #         else:
    #             mql_record = db.mql_queries[mql_record]
    #             if mql_record is None:
    #                 raise HTTP(404, "Object not found in database.")
    #             if mql_record.created_by != auth.user.id:
    #                 return False

    # if mql_record is None:
    #     mql_record = db(db.mql_queries.created_by==auth.user).select().last() or 0
    #
    # request.vars['mql_record']=mql_record
    return True


def get_mql_form(mql_record):
    mql_form = SQLFORM(db.mql_queries, record=mql_record,
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


@auth.requires(lambda: check_query_access())
def query():

    mql_record = request.vars.id
    if type(request.vars.id) == list:
        mql_record = request.vars.id[0]

    if mql_record is None:
        mql_record = db(db.mql_queries.created_by==auth.user).select().last() or 0
    else:
        mql_record = int(mql_record)

    mql_form = get_mql_form(mql_record)

    mql_form.process(keepvalues=True)

    if mql_form.accepted:
        record_id=str(mql_form.vars.id)

        if request.vars.has_key('button_save'):
            session.flash = 'saved query as ' + record_id

        elif request.vars.has_key('button_execute'):
            session.flash = 'executing query ' +  record_id

        elif request.vars.has_key('button_new'):
            session.flash = 'saved previous query as ' + record_id
            record_id='0'

        redirect(URL('query',vars=dict(id=record_id)))

    elif mql_form.errors:
        response.flash = 'form has errors, see details'

    return dict(form=mql_form)


@auth.requires_login()
def new_query():
    print 'new query'
    mql_form = get_mql_form(None)
    mql_form._action='query'
    return dict(form=mql_form)



@auth.requires_login()
def manage_queries():
    grid = SQLFORM.grid(db.mql_queries.created_by==auth.user,
        fields={db.mql_queries.id, db.mql_queries.name, db.mql_queries.created_on,
                db.mql_queries.modified_on, db.mql_queries.modified_by},
        orderby=~db.mql_queries.modified_on,
        selectable = lambda ids : redirect(URL('linquer', 'delete_multiple', vars=dict(id=ids))),
        details=False,
        paginate=3,
        csv=False)
    return locals()


@auth.requires_login()
def delete_multiple():
    print request.vars.id
    session.flash="deleted " + str(request.vars.id)
    redirect(URL('manage_queries'))