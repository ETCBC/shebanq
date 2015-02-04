#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)
import collections, json
import xml.etree.ElementTree as ET
from itertools import groupby

from render import Verses, Viewsettings, legend, colorpicker, h_esc, get_fields
from mql import mql

# Note on caching
#
# We use web2py caching for verse material and for item lists (word lists and query lists).
#
# see: http://web2py.com/books/default/chapter/29/04/the-core#cache
#
# We also cache
# - the list of bible books
# - the table of all verse boundaries
# - all the static pages.
# We do not (yet) deliberately manage browser caching.
# We use the lower-level mechanisms of web2py: cache.ram, and refrain from decorating controllers with @cache or @cache.action,
# because we have to be selective on which request vars are important for keying the cached items.
 
# For verse material and item lists we cache the rendered view. So we do use response.render(result).
#
# Note that what the user sees, is the effect of the javascript in hebrew.js on the html produced by rendered view.
# So the cached data only has to be indexed by those request vars that select content: mr, qw, book, chapter, item id (iid) and (result) page.
# I think this strikes a nice balance:
# (a) these chunks of html are equal for all users that visit such a page, regardless of their view settings
# (b) these chunks of html are relatively small, only the material of one page.
# It is tempting to cache the SQL queries, but they fetch large amounts of data, of which only a tiny portion
# shows up. So it uses a lot of space.
# If a user examines a query with 1000 pages of results, it is unlikely that she will visit all of them, so it is not worthwhile
# to keep the results of the one big query in cache all the time.
# On the other hand, many users look at the first page of query results, and py caching individual pages, the number of times
# that the big query is exececuted is reduced significantly.
#
# Note on correctness: 
# If a user executes a query, the list of queries associated with a chapter has to be recomputed for all chapters.
# This means that ALL cached query lists of ALL chapters have to be cleared.
# So if users are active with executing queries, the caching of query lists is not very useful.
# But for those periods where nobody executes a query, all users benefit from better response times. 
# We cache in ram, but also on disk, in order to retain the cache across restarting the webserver

RESULT_PAGE_SIZE = 20

CACHING = True

def from_cache(ckey, func, expire):
    if CACHING:
        result = cache.ram(ckey, lambda:cache.disk(ckey, func, time_expire=expire), time_expire=expire)
    else:
        result = func()
    return result

def text():
    session.forget(response)
    (books, books_order) = from_cache('books', get_books, None)

    return dict(
        viewsettings=Viewsettings(),
        colorpicker=colorpicker,
        legend=legend,
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
    )

def get_books(no_controller=True): # get book information: number of chapters per book
    ckey = 'books'
    books_data = passage_db.executesql('''
select name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id;
''')
    books_order = [x[0] for x in books_data]
    books = dict(x for x in books_data)
    return (books, books_order)

def material():
    session.forget(response)
    mr = request.vars.mr
    qw = request.vars.qw
    bk = request.vars.book
    ch = request.vars.chapter
    tp = request.vars.tp
    iid = int(request.vars.iid) if request.vars.iid else None
    page = int(request.vars.page) if request.vars.page else 1
    mrrep = 'm' if mr == 'm' else qw
    ckey = 'verses_{}:{}_{}:{}:'.format(mrrep, bk if mr=='m' else iid, ch if mr=='m' else page, tp)
    return from_cache(
        'verses_{}:{}_{}:{}:'.format(mrrep, bk if mr=='m' else iid, ch if mr=='m' else page, tp),
        lambda: material_c(mr, qw, bk, iid, ch, page, tp),
        None,
    )

def material_c(mr, qw, bk, iid, ch, page, tp):
    if mr == 'm':
        (book, chapter) = getpassage()
        material = Verses(passage_db, mr, chapter=chapter.id, tp=tp) if chapter != None else None
        result = dict(
            mr=mr,
            qw=qw,
            hits=0,
            msg="No chapter selected" if not chapter else None,
            results=len(material.verses) if material else 0,
            pages=1,
            material=material,
            monads=json.dumps([]),
        )
    elif mr == 'r':
        if iid == None:
            msg = "No {} selected".format('query' if qw == 'q' else 'word')
            result = dict(
                mr=mr,
                qw=qw,
                msg=msg,
                hits=0,
                results=0,
                iid=iid,
                pages=0,
                page=0,
                pagelist=json.dumps([]),
                chart=json.dumps({}),
                chart_order=json.dumps([]),
                material=None,
                monads=json.dumps([]),
            )
        else:
            (nmonads, monad_sets) = load_monad_sets(iid) if qw == 'q' else load_word_occurrences(iid)
            (nresults, npages, verses, monads) = get_pagination(page, monad_sets, iid)
            (chart, chart_order) = from_cache(
                'chart_{}:{}:'.format(qw, iid),
                lambda: get_chart(monad_sets),
                None,
            )
            material = Verses(passage_db, mr, verses, tp=tp)
            result = dict(
                mr=mr,
                qw=qw,
                msg=None,
                hits=nmonads,
                results=nresults,
                iid=iid,
                pages=npages,
                page=page,
                pagelist=json.dumps(pagelist(page, npages, 10)),
                chart=chart,
                chart_order=chart_order,
                material=material,
                monads=json.dumps(monads),
            )
    else:
        result = dict()
    return response.render(result)

def sidem():
    session.forget(response)
    qw = request.vars.qw
    bk = request.vars.book
    ch = request.vars.chapter
    return from_cache(
        'items_{}:{}_{}:'.format(qw, bk, ch),
        lambda: sidem_c(qw, bk, ch),
        None,
    )

def sidem_c(qw, bk, ch):
    (book, chapter) = getpassage()
    if qw == 'q':
        monad_sets = get_monadsets_MySQL(chapter)
        side_items = group_MySQL(monad_sets)
    else:
        side_items = get_lexemes(chapter)
    result = dict(
        colorpicker=colorpicker,
        side_items=side_items,
        qw=qw,
    )
    return response.render(result)

def query():
    request.vars['mr'] = 'r'
    request.vars['qw'] = 'q'
    request.vars['tp'] = 'txt_p'
    request.vars['iid'] = request.vars.id or request.vars.iid
    request.vars['page'] = 1
    return text()

def word():
    request.vars['mr'] = 'r'
    request.vars['qw'] = 'w'
    request.vars['tp'] = 'txt_p'
    request.vars['iid'] = request.vars.id or request.vars.iid
    request.vars['page'] = 1
    return text()

def csv(data): # converts an data structure of rows and fields into a csv string, with proper quotations and escapes
    result = []
    if data != None:
        for row in data:
            prow = [unicode(x) for x in row]
            trow = [u'"{}"'.format(x.replace('"','""')) if '"' in x or '\n' in x or '\r' in x or ',' in x else x for x in prow]
            result.append(u','.join(trow))
    return u'\n'.join(result)

def item(): # controller to produce a csv file of query results or lexeme occurrences, where fields are specified in the current legend
    iid = request.vars.iid
    qw = request.vars.qw
    filename = '{}_{}.csv'.format('query' if qw == 'q' else 'word', iid)
    hfields = get_fields()
    head_row = ['book', 'chapter', 'verse'] + [hf[1] for hf in hfields]
    (nmonads, monad_sets) = load_monad_sets(iid) if qw == 'q' else load_word_occurrences(iid)
    monads = flatten(monad_sets)
    data = []
    if len(monads):
        sql = '''
select 
    book.name, chapter.chapter_num, verse.verse_num,
    {hflist}
from word
inner join word_verse on
    word_verse.anchor = word.word_number
inner join verse on
    verse.id = word_verse.verse_id
inner join chapter on
    verse.chapter_id = chapter.id
inner join book on
    chapter.book_id = book.id
where
    word.word_number in ({monads})
order by
    word.word_number
'''.format(
            hflist=', '.join('word.{}'.format(hf[0]) for hf in hfields),
            monads=','.join(monads),
        )
        data = passage_db.executesql(sql)
    return dict(filename=filename, data=csv((head_row,)+data))

def sideqm():
    session.forget(response)
    iid = request.vars.iid or request.vars.id
    return dict(load=LOAD('hebrew', 'sideq', extension='load',
        vars=dict(mr='r', qw='q', iid=iid),
        ajax=False, ajax_trap=True, target='querybody', 
        content='fetching query',
    ))

def sidewm():
    session.forget(response)
    iid = request.vars.iid or request.vars.id
    return dict(load=LOAD('hebrew', 'sidew', extension='load',
        vars=dict(mr='r', qw='w', iid=iid),
        ajax=False, ajax_trap=True, target='wordbody', 
        content='fetching words',
    ))

@auth.requires(lambda: check_query_access_write())
def sideqe():
    if not request.is_local: request.requires_https()
    return show_query(readonly=False)

def sideq():
    session.forget(response)
    return show_query(readonly=True)

def sidew():
    session.forget(response)
    return show_word()

def dictionary():
    lan = request.vars.lan
    letter = request.vars.letter
    if lan == None: lan = 'hbo'
    if letter == None: letter = 1488 
    else: letter = int(letter)
    return from_cache(
        'dictionary_page_{}_{}:'.format(lan, letter),
        lambda: dictionary_page(lan, letter),
        None,
    )

def dictionary_page(lan=None, letter=None):
    (letters, words) = from_cache('dictionary_data', lambda: get_dictionary_data(), None)
    return response.render(dict(lan=lan, letter=letter, letters=letters, words=words[lan][letter]))

def get_dictionary_data():
    ddata = passage_db.executesql('''
select id, entry_heb, entryid_heb, lan, gloss from lexicon
order by lan, entryid_heb
''')
    letters = dict(arc=[], hbo=[])
    words = dict(arc={}, hbo={})
    for (id, e, eid, lan, gloss) in ddata:
        letter = ord(e[0])
        if letter not in words[lan]:
            letters[lan].append(letter)
            words[lan][letter] = []
        words[lan][letter].append((e, id, eid, gloss))
    return (letters, words)

@auth.requires_login()
def my_queries():
    if not request.is_local: request.requires_https()
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
        editable=True,
        details=False,
        create=True,
        links=[
            dict(
                header='view',
                body=lambda row: A(
                    SPAN(_class='icon info-sign icon-info-sign'),
                    SPAN('', _class='buttontext button', _title='View'),
                    _class='button btn',
                    _href=URL('hebrew', 'text', vars=dict(mr='r', qw='q', iid=row.id, page=1)),
                ) 
            ),
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
    if not request.is_local: request.requires_https()
    if request.vars.id is not None:
        for id in request.vars.id:
            db(db.queries.id == id).delete()

    response.flash = "deleted " + str(request.vars.id)
    redirect(URL('my_queries'))

def show_query(readonly=True, kind=None, msg=None):
    response.headers['web2py-component-flash']=None
    iid = get_iid()
    if iid:
        old_mql = db.queries[iid].mql
        old_modified_on = db.queries[iid].modified_on
    else:
        iid = 0
        old_mql = ''
        old_modified_on = 0
    mql_form = get_mql_form(iid, readonly=readonly)
    (thisreadonly, thiskind, thismsg) = handle_response_mql(mql_form, old_mql, old_modified_on)
    if thisreadonly != None: readonly = thisreadonly
    if thiskind != None: kind = thiskind
    if thismsg != None: msg = thismsg
    mql_record = db.queries[iid]

    return dict(
        readonly=readonly,
        kind=kind,
        msg=msg,
        form=mql_form,
        iid=iid,
        query=mql_record,
    )

def show_word(no_controller=True):
    response.headers['web2py-component-flash']=None
    iid = get_iid()
    word_form = get_word_form(iid)
    handle_response_word(word_form)
    word_record = passage_db.lexicon[iid]

    result_dict = dict(
        readonly=True,
        form=word_form,
        iid=iid,
        word=word_record,
        msg=None,
    )
    return result_dict

@auth.requires(lambda: check_query_access_execute())
def execute_query(iid):
    mql_form = get_mql_form(iid, readonly=False)
    mql_record = db.queries[iid]
    (good, result) = mql(mql_record.mql) 
    if good:
        store_monad_sets(iid, result)
        mql_record.update_record(executed_on=request.now)
        (kind, msg) = ('ok', 'Query executed')
    else:
        (kind, msg) = ('error', CODE(result))
    return (kind, msg)

def pagelist(page, pages, spread):
    factor = 1
    filtered_pages = {1, page, pages}
    while factor <= pages:
        page_base = factor * int(page / factor)
        filtered_pages |= {page_base + int((i - spread / 2) * factor) for i in range(2 * int(spread / 2) + 1)} 
        factor *= spread
    return sorted(i for i in filtered_pages if i > 0 and i <= pages) 

def flatten(msets):
    result = set()
    for (b,e) in msets:
        for m in range(b, e+1):
            result.add(str(m))
    return list(sorted(result))

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

def get_iid(no_controller=True):
    # web2py returns hidden id and (if present) id in URL, so id can be None, str or list(str)
    iid = request.vars.id or request.vars.iid
    if iid is not None:
        if type(iid) == list:
            iid = int(iid[0])
        else:
            iid = int(iid)
    return iid


@auth.requires_login()
def check_query_access_write(iid=get_iid()):
    authorized = True

    if iid is not None and iid > 0:
        mql_record = db.queries[iid]
        if mql_record is None:
            raise HTTP(404, "No write access. Object not found in database. id=" + str(iid))
        if mql_record.created_by != auth.user.id:
            authorized = False

    return authorized


@auth.requires_login()
def check_query_access_execute(iid=get_iid()):
    authorized = False

    if iid is not None and iid > 0:
        mql_record = db.queries[iid]
        if mql_record is None:
            raise HTTP(404, "No execute access. Object not found in database. id=" + str(iid))
        if mql_record.created_by == auth.user.id:
            authorized = True

    return authorized


def get_mql_form(iid, readonly=False):
    mql_record = db.queries[iid]
    buttons = [
        TAG.button('Reset', _class="smb", _type='reset', _name='button_reset'),
        TAG.button('Save', _class="smb", _type='submit', _name='button_save'),
        TAG.button('Execute', _class="smb", _type='submit', _name='button_execute'),
        TAG.button('Done', _class="smb", _type='submit', _name='button_done'),
    ]
    qedit_link = ''
    medit_link = ''
    if auth.user and auth.user.id == mql_record.created_by:
        if readonly:
            qedit_link = A(
                SPAN(_class='icon pen icon-pencil'),
                SPAN('Edit query', _class='buttontext button', _title='Edit query'),
                _class='button btn',
                _href=URL('hebrew', 'sideqe', vars=dict(mr='r', qw='q', iid=iid)),
                cid=request.cid,
            )
        medit_link = A(
            SPAN(_class='icon pen icon-pencil'),
            SPAN('', _class='buttontext button', _title='Edit all fields'),
            SPAN('Edit info', _class='buttontext button', _title='Edit all info fields'),
            _class='button btn',
            _href=URL('hebrew', 'my_queries', extension='', args=['edit', 'queries', iid], user_signature=True),
        )
    else:
        qedit_link = 'You cannot edit queries created by some one else'
        qedit_link = P(A(
            SPAN(_class='icon resize-full icon-resize-full'),
            _class='ctrl fullc fullcp',
            _href='#',
            _id='readq_{}'.format(iid),
        ), _class='fullcpx')
        medit_link = ''
    mql_form = SQLFORM(db.queries, record=iid, readonly=readonly,
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
        ] if readonly else [
            'is_published',
            'name',
            'description',
            'mql',
        ],
        showid=False, ignore_rw=False,
        col3 = dict(
            mql=qedit_link,
            name=medit_link,
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

def get_word_form(iid):
    word_record = passage_db.lexicon[iid]
    word_form = SQLFORM(passage_db.lexicon, record=iid, readonly=True,
        fields=[
            'g_entry_heb',
            'g_entry',
            'entry_heb',
            'entry',
            'entryid_heb',
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
            g_entry_heb='vocalized-hebrew',
            g_entry='vocalized-translit',
            entry_heb='consonantal-hebrew',
            entry='consonantal-translit',
            entryid_heb='disambiguated-hebrew',
            entryid='disambiguated-translit',
            pos='part-of-speech',
            subpos='lexical set',
            nametype='proper noun category',
            lan='language',
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
    readonly = None
    msg = None
    kind = None
    mql_form.process(keepvalues=True, onvalidation=fiddle_dates(old_mql, old_modified_on), onsuccess=lambda f:None, onfailure=lambda f: None)
    if mql_form.accepted:
        iid = str(mql_form.vars.id)
        if request.vars.button_execute == 'true':
            (kind, msg) = execute_query(iid) 
        if request.vars.button_save == 'true':
            (kind, msg) = ('ok', 'saved')
        if request.vars.button_done == 'true':
            redirect(URL('hebrew', 'sideqm', vars=dict(mr='r', qw='q', iid=iid), extension=''))
    elif mql_form.errors:
        (kind, msg) = ('error', 'make corrections as indicated above')
    return (readonly, kind, msg)

def handle_response_word(word_form):
    word_form.process(keepvalues=True)
    if word_form.accepted:
        pass
    elif word_form.errors:
        response.flash = 'form has errors, see details'

def store_monad_sets(iid, rows):
    db.executesql('DELETE FROM monadsets WHERE query_id=' + str(iid) + ';')
    # Here we clear stuff that will become invalid because of a (re)execution of a query
    # and the deleting of previous results and the storing of new results.
    ckeys = r'^verses_q:{}_'.format(iid)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    ckeys = r'^items_q:'
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    ckeys = r'^chart_q:{}:'.format(iid)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    nrows = len(rows)
    if nrows == 0: return

    limit_row = 10000
    start = '''
insert into monadsets (query_id, first_m, last_m) values
'''
    query = ''
    r = 0
    while r < nrows:
        if query != '':
            db.executesql(query)
            query = ''
        query += start
        s = min(r + limit_row, len(rows))
        row = rows[r]
        query += '({},{},{})'.format(iid, row[0], row[1])
        if r + 1 < nrows:
            for row in rows[r + 1:s]: 
                query += ',({},{},{})'.format(iid, row[0], row[1])
        r = s
    if query != '':
        db.executesql(query)
        query = ''

def load_monad_sets(iid):
    monad_sets = db.executesql('SELECT first_m, last_m FROM monadsets WHERE query_id=' + str(iid) + ' ORDER BY first_m;')
    return normalize_ranges(monad_sets)

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
    return (len(covered), result)

def get_pagination(p, monad_sets, iid):
    verse_boundaries = from_cache(
        'verse_boundaries',
        lambda: passage_db.executesql('SELECT first_m, last_m FROM verse ORDER BY id;'),
        None,
    )
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

def get_chart(monad_sets): # get data for a chart of the monadset: organized by book and chapter
    monads = flatten(monad_sets)
    data = []
    chart = {}
    chart_order = []
    if len(monads):
        sql = '''
select 
    book.name, chapter.chapter_num
from word
inner join word_verse on
    word_verse.anchor = word.word_number
inner join verse on
    verse.id = word_verse.verse_id
inner join chapter on
    verse.chapter_id = chapter.id
inner join book on
    chapter.book_id = book.id
where
    word.word_number in ({monads})
order by
    word.word_number
'''.format(
            monads=','.join(monads),
        )
        data = passage_db.executesql(sql)
        (books, books_order) = from_cache('books', lambda: get_books(), None)

        for b in books_order:
            chart[b] = [0 for c in range(books[b])]
            chart_order.append(b)
        for (b, ch) in data:
            chart[b][int(ch)-1] += 1

    return (json.dumps(chart), json.dumps(chart_order))


