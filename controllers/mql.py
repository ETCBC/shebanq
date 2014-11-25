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

RESULT_PAGE_SIZE = 20

from gluon.custom_import import track_changes; track_changes(True)
import json
import xml.etree.ElementTree as ET

from render import Verses, Viewsettings
from shemdros import MqlResource, RemoteException

def get_record_id():
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


def get_mql_form(record_id, readonly=False):
    mql_record = db.queries[record_id]
    buttons = [
        TAG.button('Reset', _type='reset', _name='button_reset'),
        TAG.button('Save', _type='submit', _name='button_save'),
        TAG.button('Execute', _type='submit', _name='button_execute'),
        TAG.button('Done', _type='submit', _name='button_done'),
    ]
    edit_link = ''
    if readonly:
        if auth.user and auth.user.id == mql_record.created_by:
            edit_link = A(
                SPAN(_class='icon pen icon-pencil'),
                SPAN('', _class='buttontext button', _title='Edit'),
                _class='button btn',
                _href=URL('mql', 'edit_query', vars=dict(id=record_id)),
            ),
            #A('Edit', _href=URL('mql', 'edit_query', vars=dict(id=record_id)))
        else:
            edit_link = 'You cannot edit queries created by some one else'

    mql_form = SQLFORM(db.queries, record=record_id, readonly=readonly,
        fields=[
            'project',
            'organization',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
            'executed_on',
            'name',
            'is_published',
            'description',
            'mql',
        ],
        showid=False, ignore_rw=False,
        col3 = dict(
            mql=edit_link,
        ),
        labels=dict(
            mql='MQL Query',
            is_published='Public',
            created_by='by',
            modified_by='by',
            created_on='created',
            modified_on='modified',
            executed_on='executed',
        ),
        formstyle='divs',
        buttons=buttons
    )
    return mql_form

def fiddle_dates(old_mql, old_modified_on):
    def _fiddle_dates(mql_form):
        mql = mql_form.vars.mql
        modified_on = mql_form.vars.modified_on
        if mql == old_mql:
            mql_form.vars.modified_on = old_modified_on
    return _fiddle_dates

def handle_response(mql_form, old_mql, old_modified_on):
    mql_form.process(keepvalues=True, onvalidation=fiddle_dates(old_mql, old_modified_on))
    if mql_form.accepted:
        record_id = str(mql_form.vars.id)

        if 'button_execute' in request.vars:
            return execute_query(record_id) 

        if 'button_save' in request.vars:
            redirect(URL('edit_query', vars=dict(id=record_id)))
        else:
            redirect(URL('display_query', vars=dict(id=record_id)))


    elif mql_form.errors:
        response.flash = 'form has errors, see details'


def store_monad_sets(record_id, monad_sets):
    db.executesql('DELETE FROM monadsets WHERE query_id=' + str(record_id) + ';')
    #db.monadsets.delete(record_id)
    for monad_set in monad_sets:
        db.monadsets.insert(query_id=record_id, first_m=monad_set[0], last_m=monad_set[1])

def load_monad_sets(record_id):
    return db.executesql('SELECT first_m, last_m FROM monadsets WHERE query_id=' + str(record_id) + ';')

def normalize_ranges(ranges):
    covered = set()
    for (start, end) in ranges:
        for i in range(start, end + 1): covered.add(i)
    cur_start = None
    cur_end = None
    result = []
    for i in sorted(covered):
        if i not in covered:
            if cur_end != None: result.append((cur_start, cur_end - 1))
            cur_start = None
            cur_end = None
        elif cur_end == None or i > cur_end:
            if cur_end != None: result.append((cur_start, cur_end - 1))
            cur_start = i
            cur_end = i + 1
        else: cur_end = i + 1
    if cur_end != None: result.append((cur_start, cur_end - 1))
    return result

def get_pagination(p, monad_sets, vid):
    verse_boundaries = passage_db.executesql('SELECT first_m, last_m FROM verse ORDER BY id;')
    m = 0 # monad range index, walking through monad_sets
    v = 0 # verse id, walking through verse_boundaries
    nvp = 0 # number of verses added to current page
    nvt = 0 # number of verses added in total
    lm = len(monad_sets)
    lv = len(verse_boundaries)
    cur_page = 1 # current page
    verse_ids = []
    verse_monads = set()
    verse_data = []
    last_v = -1
    while m < lm and v < lv:
        if nvp == RESULT_PAGE_SIZE:
            nvp = 0
            cur_page += 1
        (v_b, v_e) = verse_boundaries[v]
        (m_b, m_e) = monad_sets[m]
        if v_e < m_b:
            v += 1
            continue
        if m_e < v_b:
            m += 1
            continue
        # now v_e >= m_b and m_e >= v_b so one of the following holds
        #           vvvvvv
        #       mmmmm
        #       mmmmmmmmmmmmmmm
        #            mmm
        #            mmmmmmmmmmmmm
        # so (v_b, v_e) and (m_b, m_e) overlap
        # so add v to the result pages and go to the next verse
        # and add p to the highlight list if on the selected page
        if v != last_v:
            if cur_page == p:
                verse_ids.append(v)
                last_v = v
            nvp += 1
            nvt += 1
        if last_v == v:
            clipped_m = set(range(max(v_b, m_b), min(v_e, m_e) + 1))
            verse_monads |= clipped_m
        if cur_page != p:
            v +=1
        else:
            if m_e < v_e:
                m += 1
            else:
                v += 1

    verses = Verses(passage_db, 'query', verse_ids=verse_ids) if p <= cur_page and len(verse_ids) else None
    return (nvt, cur_page, verses, list(verse_monads))

def index():
    redirect(URL('edit_query'))


@auth.requires(lambda: check_query_access_write())
def edit_query():
    return show_query("Edit Query", False)

def display_query():
    return show_query("Display Query", True)
    record_id = get_record_id()

    mql_record = db.queries[record_id]
    person = auth.settings.table_user[mql_record.created_by]
    project = db.project[mql_record.project]
    organization = db.organization[mql_record.organization]

    result_dict = dict(
        edit=False,
        exception=None,
        vid=record_id,
        query=mql_record,
        person=person, project=project, organization=organization,
    )
    result_dict.update(show_results(record_id))
    return result_dict

def show_query(title, readonly=True):
    record_id = get_record_id()
    if record_id is None:
        record_id = 0
    mql_form = get_mql_form(record_id, readonly=readonly)
    old_mql = db.queries[record_id].mql
    old_modified_on = db.queries[record_id].modified_on
    handle_response(mql_form, old_mql, old_modified_on)
    mql_record = db.queries[record_id]
    query = mql_record.mql

    response.title = T(title)

    result_dict = dict(
        readonly=readonly,
        form=mql_form,
        exception=None,
        vid=record_id,
        query=mql_record,
    )
    result_dict.update(show_results(record_id))
    return result_dict

@auth.requires(lambda: check_query_access_execute())
def execute_query(record_id):
    mql_form = get_mql_form(record_id, readonly=False)
    mql_record = db.queries[record_id]
    monad_sets = None
    mql = MqlResource()
    try:
        monad_sets = mql.list_monad_set(mql_record.mql)
        store_monad_sets(record_id, normalize_ranges(monad_sets))
    except RemoteException, e:
        response.flash = 'Exception while executing query: '
        return dict(
            edit=True, form=mql_form, vid=record_id, query=mql_record,
            exception=CODE(e.message), exception_message=CODE(parse_exception(e.response.text)),
            results=0,
            pages=0, page=0, pagelist=[],
            verse_data=[],
            viewsettings=None,
            page_kind='query',
        )

    mql_record.update_record(executed_on=request.now)
    redirect(URL('edit_query', vars=dict(id=record_id)))
    return show_query("Query Executed", readonly=False)

def show_results(record_id):
    page = response.vars.page if response.vars else 1
    monad_sets = load_monad_sets(record_id)
    (nresults, npages, verse_data, monads) = get_pagination(page, monad_sets, record_id)
    viewsettings = Viewsettings('query', vid=record_id)
    return dict(
        vid=record_id,
        results=nresults,
        pages=npages, page=page, pagelist=pagelist(page, npages, 10),
        verse_data=verse_data,
        viewsettings=viewsettings,
        monads=json.dumps(monads),
        page_kind='query',
    )

def result_page():
    record_id = int(request.vars.id) if request.vars else -1
    page = int(request.vars.page) if request.vars else 1
    if record_id < 0:
        return dict(
            exception=None,
            vid=record_id,
            results = 0,
            pages=0, page=0, pagelist=[],
            verse_data=[],
            page_kind='query',
        )

    monad_sets = load_monad_sets(record_id)

    (nresults, npages, verse_data, monads) = get_pagination(page, monad_sets, record_id)

    return dict(
        exception=None,
        vid=record_id,
        results=nresults,
        pages=npages, page=page, pagelist=pagelist(page, npages, 10),
        verse_data=verse_data,
        monads=monads,
        page_kind='query',
    )

def pagelist(page, pages, spread):
    factor = 1
    filtered_pages = {1, page, pages}
    while factor <= pages:
        page_base = factor * int(page / factor)
        filtered_pages |= {page_base + int((i - spread / 2) * factor) for i in range(2 * int(spread / 2) + 1)} 
        factor *= spread
    return sorted(i for i in filtered_pages if i > 0 and i <= pages) 

def parse_exception(message):
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
                        fields=[db.queries.name, db.queries.is_published,
                                db.queries.modified_on, db.queries.executed_on],
                        orderby=~db.queries.modified_on,
                        sorter_icons=(XML('&#x2191;'), XML('&#x2193;')),
                        headers={
                            'queries.is_published': 'Public',
                            'queries.executed_on': 'Last Run',
                            'queries.modified_on': 'Modified',
                        },
                        selectable=[('Delete selected', lambda ids: redirect(URL('mql', 'delete_multiple', vars=dict(id=ids))))],
                        editable=False,
                        details=False,
                        create=True,
                        links=[
                            dict(
                                header='view',
                                body=lambda row: A(
                                    SPAN(_class='icon info-sign icon-info-sign'),
                                    SPAN('', _class='buttontext button', _title='View'),
                                    _class='button btn',
                                    _href=URL('mql', 'display_query', vars=dict(id=row.id)),
                                ) 
                            ),
                            dict(
                                header='edit',
                                body=lambda row: A(
                                    SPAN(_class='icon pen icon-pencil'),
                                    SPAN('', _class='buttontext button', _title='Edit'),
                                    _class='button btn',
                                    _href=URL('mql', 'edit_query', vars=dict(id=row.id)),
                                ),
                            ),
                        ],
                        showbuttontext=False,
                        paginate=20,
                        csv=False)

    if 1 in grid:
        grid[1].element(_type="submit", _value="Delete selected")["_onclick"] = "return confirm('Delete selected records?');"
    return locals()

def public_queries():
    grid = SQLFORM.grid(db.queries.is_published == True,
                        fields=[db.queries.id, db.queries.name ,db.queries.modified_by, db.queries.created_on,
                                db.queries.modified_on, db.queries.executed_on],
                        orderby=~db.queries.modified_on,
                        sorter_icons=(XML('&#x2191;'), XML('&#x2193;')),
                        headers={
                            'queries.executed_on': 'Last Run',
                            'queries.modified_on': 'Modified',
                        },
                        editable=False,
                        deletable=False,
                        details=False,
                        create=False,
                        links_placement='left',
                        links=[
                            dict(
                                header='View',
                                body=lambda row: A(
                                    row.name,
                                    _href=URL('mql', 'display_query', vars=dict(id=row.id)),
                                ) 
                            ),
                        ],
                        paginate=20,
                        csv=False)
    return locals()


@auth.requires_login()
def delete_multiple():
    if request.vars.id is not None:
        for id in request.vars.id:
            db(db.queries.id == id).delete()

    session.flash = "deleted " + str(request.vars.id)
    redirect(URL('my_queries'))
