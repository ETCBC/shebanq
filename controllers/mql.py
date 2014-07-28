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

if 0:
    from . import *
    # End of fake imports to satisfy the editor.
    #


import xml.etree.ElementTree as ET

class Verse():

    def __init__(self, book_name, chapter_num, verse_num, xml, highlights=set()):
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        self.xml = xml
        self.highlights = highlights
        self.words = []

    def to_string(self):
        return "{}\n{}".format(self.citation_ref(), self.text)

    def citation_ref(self):
        return "{} {}:{}".format(self.book_name.replace('_', ' '), self.chapter_num, self.verse_num)

    def get_words(self):
        if (len(self.words) is 0):
            root = ET.fromstring(u'<verse>{}</verse>'.format(self.xml).encode('utf-8'))
            for child in root:
                monad_id = int(child.attrib['m'])
                focus = monad_id in self.highlights
                text = '' if child.text is None else child.text
                trailer = child.get('t', '')
                word = Word(monad_id, text, trailer, focus=focus)
                self.words.append(word)
        return self.words


class Word():

    def __init__(self, monad_id, text, trailer, focus=False):
        self.monad_id = monad_id
        self.text = text
        self.trailer = trailer
        self.focus = focus

    def to_string(self):
        return "id:" + str(self.monad_id) + " focus:" + str(self.focus) + " text:" + self.text + " trailer:" + self.trailer


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
def check_query_access_read(record_id=get_record_id()):
    #print "check_query_access_write"
    authorized = True

    if record_id is not None and record_id > 0:
        mql_record = db.queries[record_id]
        if mql_record is None:
            raise HTTP(404, "No read access. Object not found in database. record_id=" + str(record_id))

    return authorized

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
                                TAG.button('Fresh results', _type='submit', _name='button_execute'),
                                TAG.button('Stored results', _type='submit', _name='button_render'),
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

def get_pagination(p, monad_sets):
    verse_boundaries = passage_db.executesql('SELECT first_m, last_m FROM verse ORDER BY id;')
    m = 0 # monad range index, walking through monad_sets
    v = 0 # verse id, walking through verse_boundaries
    nvp = 0 # number of verses added to current page
    nvt = 0 # number of verses added in total
    lm = len(monad_sets)
    lv = len(verse_boundaries)
    cur_page = 1 # current page
    verse_ids = []
    verse_monads = {}
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
        if cur_page == p:
            if v not in verse_monads: verse_monads[v] = set()
            clipped_m = set(range(max(v_b, m_b), min(v_e, m_e) + 1))
            verse_monads[v] |= clipped_m
        if cur_page != p:
            v +=1
        else:
            if m_e < v_e:
                m += 1
            else:
                v += 1
    
    if p <= cur_page:
        verse_info = passage_db.executesql('''
SELECT verse.id, book.name, chapter.chapter_num, verse.verse_num, verse.xml FROM verse
INNER JOIN chapter ON verse.chapter_id=chapter.id
INNER JOIN book ON chapter.book_id=book.id
WHERE verse.id IN ({})
ORDER BY verse.id;'''.format(','.join([str(v) for v in verse_ids]))) 
        for v in verse_info:
            v_id = int(v[0])
            verse_data.append(Verse(v[1], v[2], v[3], v[4], set(verse_monads[v_id]))) 

    return (nvt, cur_page, verse_data)


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
    return show_query(True, "Fresh results")


@auth.requires(lambda: check_query_access_read())
def render_query():
    title = "Fresh results"
    response.title = T("Stored results")
    return show_query(False, "Stored Results")

def show_query(with_execute, title):
    from shemdros.client.api import MqlResource
    from shemdros.client.api import RemoteException
#    from shebanq_db.etcbc import VerseIterator

    record_id = get_record_id()
    mql_form = get_mql_form(record_id)
    handle_response(mql_form)
    mql_record = db.queries[record_id]
    query = mql_record.mql
    page = response.vars.page if response.vars else 1

    monad_sets = None
    if with_execute:
        mql = MqlResource()
        try:
            monad_sets = mql.list_monad_set(mql_record.mql)
            store_monad_sets(record_id, normalize_ranges(monad_sets))
        except RemoteException, e:
            response.flash = 'Exception while executing query: '
            return dict(form=mql_form, exception=CODE(e.message), exception_message=CODE(parse_exception(e.response.text)))

        response.flash = 'Query executed'
    else:
        monad_sets = load_monad_sets(record_id)

    (nresults, npages, verse_data) = get_pagination(page, monad_sets)
    response.flash = '{} results on {} pages'.format(nresults, npages)
    response.title = T(title)

    return dict(
        form=mql_form, exception=None,
        qid=record_id,
        results=nresults,
        pages=npages, page=page, pagelist=pagelist(page, npages, 10),
        verse_data=verse_data
    )

@auth.requires(lambda: check_query_access_read())
def result_page():
    record_id = int(request.vars.id) if request.vars else -1
    page = int(request.vars.page) if request.vars else 1
    if record_id < 0:
        return dict(
            qid=record_id,
            results = 0,
            pages=0, page=0, pagelist=[],
            verse_data=[]
        )

    monad_sets = load_monad_sets(record_id)

    (nresults, npages, verse_data) = get_pagination(page, monad_sets)
    response.flash = '{} results on {} pages'.format(nresults, npages)

    return dict(
        qid=record_id,
        results=nresults,
        pages=npages, page=page, pagelist=pagelist(page, npages, 10),
        verse_data=verse_data
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
