#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)
import collections, json
import xml.etree.ElementTree as ET
from itertools import groupby

from render import Verses, Viewsettings, legend, colorpicker
from shemdros import MqlResource, RemoteException
RESULT_PAGE_SIZE = 20
EXPIRE = 0

def getpassage(no_controller=True):
    book_name = request.vars.book or None
    chapter_num = request.vars.chapter or None
    book = None
    chapter = None
    if book_name:
        book = passage_db.book(name=book_name)
    if chapter_num != None and book:
        chapter = passage_db.chapter(chapter_num=chapter_num, book_id=book.id)
    return (book, chapter)

def group_MySQL(input):
    """ HELPER for query_form
    Reorganise a query_monad query.

    Input (query dict):
    [
        {'query_id': 10L, 'first_m': 1L,  'last_m': 7L},
        {'query_id': 7L,  'first_m': 1L,  'last_m': 7L},
        {'query_id': 9L,  'first_m': 1L,  'last_m': 7L},
        {'query_id': 10L, 'first_m': 10L, 'last_m': 13L},
        {'query_id': 5L,  'first_m': 1L,  'last_m': 7L}
    ]
    Output (replace the query id with the actual query row object):
    [
        {'query': <Row {'query': 'Dit is query 5.', 'id': 5L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 7.', 'id': 7L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 9.', 'id': 9L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 10.', 'id': 10L, ...}>,
         'monadsets': [(1L, 7L), (10L, 15L)],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L, 10L, 11L, 12L, 13L]',},
    ]
    """
    sorted_input = sorted(input, key=lambda x: x['query_id'])
    groups = groupby(sorted_input, key=lambda x: x['query_id'])
    r = []
    for key, val in groups:
        query = db.queries(key)
        monads = [(m['first_m'], m['last_m']) for m in val]
        json_monads = json.dumps(sorted(list(set(sum([range(x[0], x[1] + 1) for x in monads], [])))))
        r.append({'item': query, 'monads': json_monads})
    return r


def get_monadsets_MySQL(chapter):
    """ HELPER to get all monadsets that relate to selected chapter.
    These will be transformed into queries with monads by 'group'.

    Output:
    [{'first_m': 296211L, 'query_id': 2L, 'last_m': 296496L},
     {'first_m': 296438L, 'query_id': 6L, 'last_m': 296438L},
     {'first_m': 296470L, 'query_id': 6L, 'last_m': 296470L},
     {'first_m': 296494L, 'query_id': 6L, 'last_m': 296494L}, ...]
    """
    return db.executesql('''
select DISTINCT
    query_id,
    GREATEST(first_m, {chapter_first_m}) as first_m,
    LEAST(last_m, {chapter_last_m}) as last_m
from
    monadsets inner join queries on
    monadsets.query_id = queries.id and queries.is_published = 'T' and queries.executed_on >= queries.modified_on
where
    (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    ({chapter_first_m} BETWEEN first_m AND last_m);
'''.format(
         chapter_last_m=chapter.last_m,
         chapter_first_m=chapter.first_m,
    ), as_dict=True)

def get_lexemes(chapter):
    lexeme_data = passage_db.executesql('''
select
    anchor, lexicon_id
from
    word_verse
where
    anchor BETWEEN {chapter_first_m} AND {chapter_last_m}
'''.format(
         chapter_last_m=chapter.last_m,
         chapter_first_m=chapter.first_m,
    ))
    grouped = collections.defaultdict(lambda: [])
    for x in lexeme_data:
        grouped[x[1]].append(x[0])
    r = []
    for lex_id in grouped:
        lexeme = passage_db.lexicon(lex_id)
        r.append({'item': lexeme, 'monads': json.dumps(grouped[lex_id])})
    return r

def sidem():
    qw = request.vars.qw
    (book, chapter) = getpassage()
    if qw == 'q':
        monadsets = get_monadsets_MySQL(chapter)
        side_items = group_MySQL(monadsets)
    else:
        side_items = get_lexemes(chapter)
    return dict(
        colorpicker=colorpicker,
        side_items=side_items,
        qw=qw,
    )

def material():
    mr = request.vars.mr
    qw = request.vars.qw
    tp = request.vars.tp
    if mr == 'm':
        (book, chapter) = getpassage()
        material = Verses(passage_db, mr, chapter=chapter.id, tp=tp) if chapter else None
        result = dict(
            mr=mr,
            qw=qw,
            exception_message="No chapter selected" if not chapter else None,
            exception=None,
            results=len(material.verses) if material else 0,
            pages=1,
            material=material,
            monads=json.dumps([]),
        )
    elif mr == 'r':
        iid = int(request.vars.iid) if request.vars else None
        page = int(request.vars.page) if request.vars.page else 1
        if iid == None:
            exception_message = "No {} selected".format('query' if qw == 'q' else 'word')
            return dict(
                mr=mr,
                qw=qw,
                exception_message=exception_message,
                exception=None,
                results=0,
                iid=iid,
                pages=0,
                page=0,
                pagelist=json.dumps([]),
                material=None,
                monads=json.dumps([]),
            )
        monad_sets = load_monad_sets(iid) if qw == 'q' else load_word_occurrences(iid)
        (nresults, npages, verses, monads) = get_pagination(page, monad_sets, iid)
        material = Verses(passage_db, mr, verses, tp=tp)
        return dict(
            mr=mr,
            qw=qw,
            exception_message=None,
            exception=None,
            results=nresults,
            iid=iid,
            pages=npages,
            page=page,
            pagelist=json.dumps(pagelist(page, npages, 10)),
            material=material,
            monads=json.dumps(monads),
        )
    return result

def text():
    books_data = passage_db.executesql('''
select name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id;
    ''')

    books_order = [x[0] for x in books_data]
    books = dict(x for x in books_data)
    viewsettings = cache.ram('viewsettings', Viewsettings, time_expire=EXPIRE)
    return dict(
        viewsettings=viewsettings,
        colorpicker=colorpicker,
        legend=legend,
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
    )

def get_record_id(no_controller=True):
    # web2py returns hidden id and (if present) id in URL, so id can be None, str or list(str)
    record_id = request.vars.iid
    if request.vars.iid is not None:
        if type(request.vars.iid) == list:
            record_id = int(request.vars.iid[0])
#        elif request.vars.iid.isdigit():
        else:
            record_id = int(request.vars.iid)
#            raise HTTP(404, "get_record_id: Object not found in database: " + str(record_id))
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

    if record_id is not None and record_id > 0:
        mql_record = db.queries[record_id]
        if mql_record is None:
            raise HTTP(404, "No execute access. Object not found in database. record_id=" + str(record_id))
        if mql_record.created_by == auth.user.id:
            authorized = True

    return authorized


def get_mql_form(record_id, readonly=False):
    mql_record = db.queries[record_id]
    buttons = [
        TAG.button('Reset', _class="smb", _type='reset', _name='button_reset'),
        TAG.button('Save', _class="smb", _type='submit', _name='button_save'),
        TAG.button('Execute', _class="smb", _type='submit', _name='button_execute'),
        TAG.button('Done', _class="smb", _type='submit', _name='button_done'),
    ]
    edit_link = ''
    if readonly:
        if auth.user and auth.user.id == mql_record.created_by:
            edit_link = A(
                SPAN(_class='icon pen icon-pencil'),
                SPAN('', _class='buttontext button', _title='Edit'),
                _class='button btn',
                _href=URL('hebrew', 'sideqe', vars=dict(mr='r', qw='q', iid=record_id)),
                cid=request.cid,
            ),
        else:
            edit_link = 'You cannot edit queries created by some one else'
    mql_form = SQLFORM(db.queries, record=record_id, readonly=readonly,
        fields=[
            'is_published',
            'name',
            'project',
            'organization',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
            'executed_on',
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
        buttons=buttons,
    )
    extra = DIV(
        INPUT(_id='button_reset', _name='button_reset',value=False,_type='hidden'),
        INPUT(_id='button_save', _name='button_save',value=False,_type='hidden'),
        INPUT(_id='button_execute', _name='button_execute',value=False,_type='hidden'),
        INPUT(_id='button_done', _name='button_done',value=False,_type='hidden'),
    )
    if not readonly:
        mql_form[0].insert(-1,extra)
    return mql_form

def get_word_form(record_id):
    word_record = passage_db.lexicon[record_id]
    word_form = SQLFORM(passage_db.lexicon, record=record_id, readonly=True,
        fields=[
            'g_entry_heb',
            'g_entry',
            'entry_heb',
            'entry',
            'entryid',
            'pos',
            'subpos',
            'nametype',
            'root',
            'lan',
            'gloss',
        ],
        showid=False, ignore_rw=False,
        labels=dict(
            g_entry_heb='Vocalized Lexeme',
            g_entry='Vocalized Lexeme (trans)',
            entry_heb='Consonantal',
            entry='Consonantal (trans)',
            entryid='With disambiguation',
            pos='part-of-speech',
            subpos='lexical set',
            nametype='proper noun category',
            lan='Language',
            gloss='gloss',
        ),
        formstyle='table3cols',
    )
    return word_form

def fiddle_dates(old_mql, old_modified_on):
    def _fiddle_dates(mql_form):
        mql = mql_form.vars.mql
        modified_on = mql_form.vars.modified_on
        if mql == old_mql:
            mql_form.vars.modified_on = old_modified_on
    return _fiddle_dates

def handle_response_mql(mql_form, old_mql, old_modified_on):
    mql_form.process(keepvalues=True, onvalidation=fiddle_dates(old_mql, old_modified_on))
    if mql_form.accepted:
        record_id = str(mql_form.vars.id)
        if request.vars.button_execute == 'true':
            return execute_query(record_id) 
        if request.vars.button_save == 'true':
            pass
        if request.vars.button_done == 'true':
            redirect(URL('hebrew', 'sideq', vars=dict(mr='r', qw='q', iid=record_id)))
    elif mql_form.errors:
        response.flash = 'form has errors, see details'

def handle_response_word(word_form):
    word_form.process(keepvalues=True)
    if word_form.accepted:
        pass
    elif word_form.errors:
        response.flash = 'form has errors, see details'

def store_monad_sets(record_id, monad_sets):
    db.executesql('DELETE FROM monadsets WHERE query_id=' + str(record_id) + ';')
    #db.monadsets.delete(record_id)
    for monad_set in monad_sets:
        db.monadsets.insert(query_id=record_id, first_m=monad_set[0], last_m=monad_set[1])

def load_monad_sets(record_id):
    return db.executesql('SELECT first_m, last_m FROM monadsets WHERE query_id=' + str(record_id) + ';')

def load_word_occurrences(lexeme_id):
    monads = passage_db.executesql('SELECT anchor FROM word_verse WHERE lexicon_id = {} ORDER BY anchor;'.format(lexeme_id))
    return collapse_into_ranges(monads)

def collapse_into_ranges(monads):
    covered = set()
    for (start,) in monads:
        covered.add(start)
    return normalize_ranges(None, fromset=covered)
    
def normalize_ranges(ranges, fromset=None):
    covered = set()
    if fromset != None:
        covered = fromset
    else:
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

def get_pagination(p, monad_sets, iid):
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

    verses = verse_ids if p <= cur_page and len(verse_ids) else None
    return (nvt, cur_page if nvt else 0, verses, list(verse_monads))


@auth.requires(lambda: check_query_access_write())
def sideqe():
    return show_query("Edit Query", False)

def sideq():
    return show_query("Display Query", True)

def sidew():
    return show_word("Display Lexeme")

def show_query(title, readonly=True):
    response.headers['web2py-component-flash']=None
    record_id = get_record_id()
    if record_id:
        old_mql = db.queries[record_id].mql
        old_modified_on = db.queries[record_id].modified_on
    else:
        record_id = 0
        old_mql = ''
        old_modified_on = 0
    mql_form = get_mql_form(record_id, readonly=readonly)
    handle_response_mql(mql_form, old_mql, old_modified_on)
    mql_record = db.queries[record_id]

    response.title = T(title)

    result_dict = dict(
        readonly=readonly,
        form=mql_form,
        exception=None,
        iid=record_id,
        query=mql_record,
    )
    return result_dict

def show_word(title):
    response.headers['web2py-component-flash']=None
    record_id = get_record_id()
    word_form = get_word_form(record_id)
    handle_response_word(word_form)
    word_record = passage_db.lexicon[record_id]

    response.title = T(title)

    result_dict = dict(
        readonly=True,
        form=word_form,
        iid=record_id,
        word=word_record,
    )
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
            edit=True, form=mql_form, iid=record_id, query=mql_record,
            exception=CODE(e.message),
            exception_message=CODE(parse_exception(e.response.text)),
            results=0,
            pages=0, page=0, pagelist=[],
            verse_data=[],
            mr='r',
            qw='q',
        )

    mql_record.update_record(executed_on=request.now)
    return show_query("Query Executed", readonly=False)

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


def sideqm():
    iid = request.vars.iid
    return dict(load=LOAD('hebrew', 'sideq', extension='load',
        vars=dict(mr='r', qw='q', iid=iid),
        ajax=False, target='querybody', 
        content='fetching query',
    ))

def sidewm():
    iid = request.vars.iid
    return dict(load=LOAD('hebrew', 'sidew', extension='load',
        vars=dict(mr='r', qw='w', iid=iid),
        ajax=False, target='wordbody', 
        content='fetching words',
    ))

@auth.requires_login()
def my_queries():
    grid = SQLFORM.grid(
        db.queries.created_by == auth.user,
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
                header='view/edit',
                body=lambda row: A(
                    SPAN(_class='icon info-sign icon-info-sign'),
                    SPAN('', _class='buttontext button', _title='View'),
                    _class='button btn',
                    _href=URL('hebrew', 'text', vars=dict(mr='r', qw='q', iid=row.id, page=1)),
                ) 
            ),
            #dict(
            #    header='edit',
            #    body=lambda row: A(
            #        SPAN(_class='icon pen icon-pencil'),
            #        SPAN('', _class='buttontext button', _title='Edit'),
            #        _class='button btn',
            #        _href=URL('hebrew', 'sideqe', vars=dict(mr='r', qw='q', iid=row.id)),
            #    ),
            #),
        ],
        showbuttontext=False,
        paginate=20,
        csv=False,
    )

    if 1 in grid:
        grid[1].element(_type="submit", _value="Delete selected")["_onclick"] = "return confirm('Delete selected records?');"
    return locals()

def public_queries():
    grid = SQLFORM.grid(
        db.queries.is_published == True,
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
                    _href=URL('hebrew', 'text', vars=dict(mr='r', qw='q', iid=row.id, page=1)),
                ) 
            ),
        ],
        paginate=20,
        csv=False,
    )
    return locals()


@auth.requires_login()
def delete_multiple():
    if request.vars.id is not None:
        for id in request.vars.id:
            db(db.queries.id == id).delete()

    session.flash = "deleted " + str(request.vars.id)
    redirect(URL('my_queries'))


def index():
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


