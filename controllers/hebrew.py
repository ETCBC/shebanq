#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)
import collections, json, datetime
from urlparse import urlparse, urlunparse
from markdown import markdown

from render import Verses, Verse, Viewsettings, legend, colorpicker, h_esc, get_request_val, get_fields, style
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
 
# We do not cache rendered views, because the views implement tweaks that are dependent on the browser.
# So we do not use response.render(result).
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
#
# Here are the cache keys we are using:

# books_{vr}_                                   list of books plus fixed book info 
# blocks_{vr}_                                  list of 500w blocks plus boundary info
# verse_boundaries                              for each verse its starting and ending monad (word number)
# verses_{vr}_{mqw}_{bk/iid}_{ch/page}_{tp}_    verses on a material page, either for a chapter, or an occurrences page of a lexeme, or a results page of a query execution
# verse_{vr}_{bk}_{ch}_{vs}_                    a single verse in data representation
# items_{qw}_{vr}_{bk}_{ch}_                    the items (queries or words) in a sidebar list of a page that shows a chapter
# chart_{vr}_{qw}_{iid}_                        the chart data for a query or word
# words_page_{vr}_{lan}_{letter}_               the data for a word index page
# words_data_{vr}_                              the data for the main word index page


RESULT_PAGE_SIZE = 20
BLOCK_SIZE = 500
PUBLISH_FREEZE = datetime.timedelta(weeks=1)
PUBLISH_FREEZE_MSG = '1 week'
NULLDT = '____-__-__ __:__:__'

CACHING = True

def from_cache(ckey, func, expire):
    if CACHING:
        result = cache.ram(ckey, lambda:cache.disk(ckey, func, time_expire=expire), time_expire=expire)
    else:
        result = func()
    return result

def text():
    session.forget(response)
    books = {}
    books_order = {}
    for vr in versions:
        if not versions[vr]['date']: continue
        (books[vr], books_order[vr]) = from_cache('books_{}_'.format(vr), lambda:get_books(vr), None)

    return dict(
        viewsettings=Viewsettings(versions),
        versions=versions,
        colorpicker=colorpicker,
        legend=legend,
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
    )

def get_books(vr): # get book information: number of chapters per book
    books_data = passage_dbs[vr].executesql('''
select name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id;
''')
    books_order = [x[0] for x in books_data]
    books = dict(x for x in books_data)
    return (books, books_order)

def get_blocks(vr): # get block info: for each monad: to which block it belongs, for each block: book and chapter number of first word.
# possibly there are gaps between books.
    book_monads = passage_dbs[vr].executesql('''
select name, first_m, last_m from book
''')
    chapter_monads = passage_dbs[vr].executesql('''
select chapter_num, first_m, last_m from chapter
''')
    m = -1
    cur_blk_f = None
    cur_blk_size = 0
    cur_bk_index = 0
    cur_ch_index = 0
    (cur_bk, cur_bk_f, cur_bk_l) = book_monads[cur_bk_index]
    (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
    blocks = []
    block_mapping = {}

    def get_curpos_info(n):
        (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
        chapter_len = cur_ch_l - cur_ch_f + 1
        fraction = float(n - cur_ch_f) / chapter_len
        rep = '{}.Z'.format(cur_ch) if n == cur_ch_l else '{}.z'.format(cur_ch) if round(10* fraction) == 10 else '{:0.1f}'.format(cur_ch+fraction)
        return (cur_ch, rep)

    while True:
        m += 1
        if m > cur_bk_l:
            size = round((float(cur_blk_size) / BLOCK_SIZE) * 100)
            blocks.append((cur_bk, cur_blk_f, get_curpos_info(m-1), size))
            cur_blk_size = 0
            cur_bk_index += 1
            if cur_bk_index >= len(book_monads):
                break
            else:
                (cur_bk, cur_bk_f, cur_bk_l) = book_monads[cur_bk_index]
                cur_ch_index += 1
                (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
                cur_blk_f = get_curpos_info(m)
        if cur_blk_size == BLOCK_SIZE:
            blocks.append((cur_bk, cur_blk_f, get_curpos_info(m-1), 100))
            cur_blk_size = 0
        if m > cur_ch_l:
            cur_ch_index += 1
            if cur_ch_index >= len(chapter_monads):
                break
            else:
                (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
        if m < cur_bk_f: continue
        if m < cur_ch_f: continue
        if cur_blk_size == 0:
            cur_blk_f = get_curpos_info(m)
        block_mapping[m] = len(blocks)
        cur_blk_size += 1
    #h = open('/Users/dirk/Downloads/blocks.txt', 'w')
    #for (b, cf, cl, s) in blocks:
    #    h.write('{} >{} ({}-{}) {}%\n'.format(b, cf[0], cf[1], cl[1], s))
    #h.close()
    #h = open('/Users/dirk/Downloads/block_mapping.txt', 'w')
    #for m in sorted(block_mapping):
    #    h.write('{} {}\n'.format(m, block_mapping[m]))
    #h.close()
    return (blocks, block_mapping)

def material():
    session.forget(response)
    mr = get_request_val('material', '', 'mr')
    qw = get_request_val('material', '', 'qw')
    vr = get_request_val('material', '', 'version')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    tp = get_request_val('material', '', 'tp')
    iid = get_request_val('material', '', 'iid')
    (authorized, msg) = query_access_read(iid=iid)
    if not authorized:
        return dict(
            version=vr,
            mr=mr,
            qw=qw,
            msg=msg,
            hits=0,
            results=0,
            iid=iid,
            pages=0,
            page=0,
            pagelist=json.dumps([]),
            material=None,
            monads=json.dumps([]),
        )
    page = get_request_val('material', '', 'page')
    mrrep = 'm' if mr == 'm' else qw
    return from_cache(
        'verses_{}_{}_{}_{}_{}_'.format(vr, mrrep, bk if mr=='m' else iid, ch if mr=='m' else page, tp),
        lambda: material_c(vr, mr, qw, bk, iid, ch, page, tp),
        None,
    )

def material_c(vr, mr, qw, bk, iid, ch, page, tp):
    if mr == 'm':
        (book, chapter) = getpassage()
        material = Verses(passage_dbs, vr, mr, chapter=chapter['id'], tp=tp) if chapter else None
        result = dict(
            mr=mr,
            qw=qw,
            hits=0,
            msg="{} {} does not exist".format(bk, ch) if not chapter else None,
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
                material=None,
                monads=json.dumps([]),
            )
        else:
            (nmonads, monad_sets) = load_monad_sets(vr, iid) if qw == 'q' else load_word_occurrences(vr, iid)
            (nresults, npages, verses, monads) = get_pagination(vr, page, monad_sets, iid)
            material = Verses(passage_dbs, vr, mr, verses, tp=tp)
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
                material=material,
                monads=json.dumps(monads),
            )
    else:
        result = dict()
    return result

def verse():
    session.forget(response)
    msgs = []
    good = False
    vr = get_request_val('material', '', 'version')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    vs = check_int('verse', 'verse', msgs)
    if vs == None:
        return dict(good=False, msgs=msgs)
    return from_cache(
        'verse_{}_{}_{}_{}_'.format(vr, bk, ch, vs),
        lambda: verse_c(vr, bk, ch, vs, msgs),
        None,
    )

def verse_c(vr, bk, ch, vs, msgs):
    material = Verse(passage_dbs, vr, bk, ch, vs, xml=None, word_data=None, tp='txt_il', mr=None)
    good = True
    if len(material.word_data) == 0:
        msgs.append(('error', '{} {}:{} does not exist'.format(bk, ch, vs)))
        good = False
    result = dict(
        good = good,
        msgs = msgs,
        material=material,
    )
    return result

def sidem():
    session.forget(response)
    vr = get_request_val('material', '', 'version')
    qw = get_request_val('material', '', 'qw')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    pub = get_request_val('highlights', 'q', 'pub') if qw == 'q' else ''
    return from_cache(
        'items_{}_{}_{}_{}_{}_'.format(qw, vr, bk, ch, pub),
        lambda: sidem_c(vr, qw, bk, ch, pub),
        None,
    )

def sidem_c(vr, qw, bk, ch, pub):
    (book, chapter) = getpassage()
    if not chapter:
        result = dict(
            colorpicker=colorpicker,
            side_items=[],
            qw=qw,
        )
    else:
        if qw == 'q':
            monad_sets = get_monads(vr, chapter, pub)
            side_items = groupq(vr, monad_sets)
        else:
            monad_sets = get_lexemes(vr, chapter)
            side_items = groupw(vr, monad_sets)
        result = dict(
            colorpicker=colorpicker,
            side_items=side_items,
            qw=qw,
        )
    return result

def query():
    iid = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    if request.extension == 'json':
        (authorized, msg) = query_access_read(iid=iid)
        if not authorized:
            result = dict(good=False, msg=[msg])
        else:
            msgs = []
            qrecord = get_query_info(iid, vr, msgs, with_ids=False, single_version=False, po=True)
            result = dict(good=qrecord != None, msg=msgs, data=qrecord)
            return dict(data=json.dumps(result))
    else:
        request.vars['mr'] = 'r'
        request.vars['qw'] = 'q'
        request.vars['tp'] = 'txt_p'
        request.vars['vr'] = vr
        request.vars['iid'] = iid
        request.vars['page'] = 1
    return text()

def word():
    request.vars['mr'] = 'r'
    request.vars['qw'] = 'w'
    request.vars['tp'] = 'txt_p'
    request.vars['version'] = get_request_val('material', '', 'version')
    request.vars['iid'] = get_request_val('material', '', 'iid')
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
    vr = get_request_val('material', '', 'version')
    iid = get_request_val('material', '', 'iid')
    qw = get_request_val('material', '', 'qw')
    filename = '{}{}.csv'.format(style[qw]['t'], iid)
    (authorized, msg) = query_access_read(iid=iid)
    if not authorized:
        return dict(filename=filename, data=msg)
    hfields = get_fields()
    head_row = ['book', 'chapter', 'verse'] + [hf[1] for hf in hfields]
    (nmonads, monad_sets) = load_monad_sets(vr, iid) if qw == 'q' else load_word_occurrences(vr, iid)
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
            hflist=u', '.join(u'word.{}'.format(hf[0]) for hf in hfields),
            monads=','.join(str(x) for x in monads),
        )
        data = passage_dbs[vr].executesql(sql)
    return dict(filename=filename, data=csv([head_row]+data))

def chart(): # controller to produce a chart of query results or lexeme occurrences
    vr = get_request_val('material', '', 'version')
    iid = get_request_val('material', '', 'iid')
    qw = get_request_val('material', '', 'qw')
    (authorized, msg) = query_access_read(iid=iid)
    if not authorized:
        result = get_chart(vr, [])
        result.update(qw=qw)
        return result()
    return from_cache(
        'chart_{}_{}_{}_'.format(vr, qw, iid),
        lambda: chart_c(vr, qw, iid),
        None,
    )

def chart_c(vr, qw, iid): 
    (nmonads, monad_sets) = load_monad_sets(vr, iid) if qw == 'q' else load_word_occurrences(vr, iid)
    result = get_chart(vr, monad_sets)
    result.update(qw=qw)
    return result

def sideqm():
    session.forget(response)
    iid = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (authorized, msg) = query_access_read(iid=iid)
    if authorized:
        msg = 'fetching query'
    return dict(load=LOAD('hebrew', 'sideq', extension='load',
        vars=dict(mr='r', qw='q', version=vr, iid=iid),
        ajax=False, ajax_trap=True, target='querybody', 
        content=msg,
    ))

def sidewm():
    session.forget(response)
    iid = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (authorized, msg) = query_access_read(iid=iid)
    if authorized:
        msg = 'fetching word'
    return dict(load=LOAD('hebrew', 'sidew', extension='load',
        vars=dict(mr='r', qw='w', version=vr, iid=iid),
        ajax=False, ajax_trap=True, target='wordbody', 
        content=msg,
    ))

def words():
    viewsettings = Viewsettings(versions)
    vr = get_request_val('material', '', 'version', default=False)
    if not vr:
        vr = viewsettings.theversion()
    lan = get_request_val('rest', '', 'lan')
    letter = get_request_val('rest', '', 'letter')
    return from_cache(
        'words_page_{}_{}_{}_'.format(vr, lan, letter),
        lambda: words_page(viewsettings, vr, lan, letter),
        None,
    )

def queries():
    msgs = []
    qid = check_id('goto', 'query', msgs)
    if qid != None:
        if not query_auth_read(qid):
            qid = None
    return dict(qid=qid if qid != None else 0)

def words_page(viewsettings, vr, lan=None, letter=None):
    (letters, words, entrymap) = from_cache('words_data_{}_'.format(vr), lambda: get_words_data(vr), None)
    return dict(versionstate=viewsettings.versionstate(), lan=lan, letter=letter, letters=letters, words=words.get(lan, {}).get(letter, []))

def get_words_data(vr):
    ddata = passage_dbs[vr].executesql('''
select id, entry_heb, entryid_heb, lan, gloss from lexicon
order by lan, entryid_heb
''')
    letters = dict(arc=[], hbo=[])
    words = dict(arc={}, hbo={})
    entrymap = dict(arc={}, hbo={})
    for (wid, e, eid, lan, gloss) in ddata:
        letter = ord(e[0])
        if letter not in words[lan]:
            letters[lan].append(letter)
            words[lan][letter] = []
        words[lan][letter].append((e, wid, eid, gloss))
        entrymap[lan][eid] = wid
    return (letters, words, entrymap)

def pq():
    myid = None
    if auth.user:
        myid = auth.user.id
    vr = get_request_val('material', '', 'version')
    return pq_c(vr, myid)

def pq_c(vr, myid):
    linfo = collections.defaultdict(lambda: {})

    def title_badge(myid, lid, ltype, newtype, good, warn, err, num, tot):
        name = linfo[ltype][lid] if ltype != None else 'Public Queries'
        nums = []
        if good != 0: nums.append(u'<span class="good">{}</span>'.format(good))
        if warn != 0: nums.append(u'<span class="warning">{}</span>'.format(warn))
        if err != 0: nums.append(u'<span class="error">{}</span>'.format(err))
        badge = ''
        if len(nums) == 1:
            if tot == num:
                badge = u'<span class="total">{}</span>'.format('+'.join(nums))
            else:
                badge = u'{} of <span class="total">{}</span>'.format('+'.join(nums), tot)
        else:
            if tot == num:
                badge = u'{}=<span class="total">{}</span>'.format('+'.join(nums), num)
            else:
                badge = u'{}={} of <span class="total">{}</span>'.format('+'.join(nums), num, tot)
        rename = ''
        create = ''
        select = ''
        if myid != None:
            if newtype != None:
                create = u'<a class="n_{}" href="#"></a>'.format(newtype)
            if ltype in {'o', 'p'}:
                if lid:
                    rename = u'<a class="r_{}" lid="{}" href="#"></a>'.format(ltype, lid)
                select = u'<a class="s_{}" lid="{}" href="#"></a>'.format(ltype, lid)
        return u'<span n="1">{}</span>{}<span class="brq">({})</span>{}{}'.format(h_esc(name), create, badge, rename, select)

    condition = '''
where query.is_shared = 'T'
''' if myid == None else '''
where query.is_shared = 'T' or query.created_by = {}
'''.format(myid)

    pqueries_sql = '''
select
    organization.name as oname, organization.id as oid,
    project.name as pname, project.id as pid,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname, auth_user.id as uid,
    query.name as qname, query.id as qid,
    query_exe.modified_on as qmod, query_exe.executed_on as qexe,
    query_exe.is_published as qpub
from query
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{}'
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
inner join auth_user on query.created_by = auth_user.id
{}
'''.format(vr, condition)
    pqueries = db.executesql(pqueries_sql)

    porg_sql = '''
select
    name, id
from organization
'''
    porg = db.executesql(porg_sql)

    pproj_sql = '''
select
    name, id
from project
'''
    pproj = db.executesql(pproj_sql)

    tree = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [])))
    countset = collections.defaultdict(lambda: set())
    counto = collections.defaultdict(lambda: 0)
    counto_good = collections.defaultdict(lambda: 0)
    counto_warn = collections.defaultdict(lambda: 0)
    counto_err = collections.defaultdict(lambda: 0)
    counto_tot = collections.defaultdict(lambda: 0)
    countp = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_good = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_warn = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_err = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_tot = collections.defaultdict(lambda: 0)
    countu = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_good = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_warn = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_err = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_tot = collections.defaultdict(lambda: 0)
    count = 0
    count_good = 0
    count_warn = 0
    count_err = 0
    for (oname, oid, pname, pid, uname, uid, qname, qid, qmod, qexe, qpub) in pqueries:
        countset['o'].add(oid)
        countset['p'].add(pid)
        countset['u'].add(uid)
        countset['q'].add(qid)
        linfo['o'][oid] = oname
        linfo['p'][pid] = pname
        linfo['u'][uid] = uname
        qownstatus = ''
        if uid == myid:
            countset['m'].add(qid)
            qownstatus = 'qmy'
        qpubstatus = ''
        if qpub != 'T':
            countset['r'].add(qid)
            qpubstatus = 'qpriv'
        if qexe:
            if qexe < qmod:
                qexestatus = 'error'
                countu_err[oid][pid][uid] += 1
                countp_err[oid][pid] += 1
                counto_err[oid] += 1
                count_err += 1
            else:
                qexestatus = 'good'
                countu_good[oid][pid][uid] += 1
                countp_good[oid][pid] += 1
                counto_good[oid] += 1
                count_good += 1
        else:
            qexestatus = 'warning'
            countu_warn[oid][pid][uid] += 1
            countp_warn[oid][pid] += 1
            counto_warn[oid] += 1
            count_warn += 1
        linfo['q'][qid] = (qname, qownstatus, qpubstatus, qexestatus)
        tree[oid][pid][uid].append(qid)
        count +=1
        counto[oid] += 1
        countp[oid][pid] += 1
        countu[oid][pid][uid] += 1
        counto_tot[oid] += 1
        countp_tot[pid] += 1
        countu_tot[uid] += 1

    linfo['o'][0] = 'Projects without Queries'
    linfo['p'][0] = 'New Project'
    linfo['u'][0] = ''
    linfo['q'][0] = ('', '', '', '')
    counto[0] = 0
    countp[0][0] = 0
    for (oname, oid) in porg:
        if oid in linfo['o']: continue
        countset['o'].add(oid)
        linfo['o'][oid] = oname
        tree[oid] = collections.defaultdict(lambda: collections.defaultdict(lambda: []))

    for (pname, pid) in pproj:
        if pid in linfo['p']: continue
        countset['o'].add(0)
        countset['p'].add(pid)
        linfo['p'][pid] = pname
        tree[0][pid] = collections.defaultdict(lambda: [])

    ccount = dict((x[0], len(x[1])) for x in countset.items())
    ccount['uid'] = myid
    title = title_badge(myid, None, None, 'o', count_good, count_warn, count_err, count, count)
    dest = [dict(title=u'{}'.format(title), folder=True, children=[], data=ccount)]
    curdest = dest[-1]['children']
    cursource = tree
    for oid in cursource:
        onum = counto[oid]
        ogood = counto_good[oid]
        owarn = counto_warn[oid]
        oerr = counto_err[oid]
        otot = counto_tot[oid]
        otitle = title_badge(myid, oid, 'o', 'p', ogood, owarn, oerr, onum, otot)
        curdest.append(dict(title=u'{}'.format(otitle), folder=True, children=[]))
        curodest = curdest[-1]['children']
        curosource = cursource[oid]
        for pid in curosource:
            pnum = countp[oid][pid]
            pgood = countp_good[oid][pid]
            pwarn = countp_warn[oid][pid]
            perr = countp_err[oid][pid]
            ptot = countp_tot[pid]
            ptitle = title_badge(myid, pid, 'p', 'q', pgood, pwarn, perr, pnum, ptot)
            curodest.append(dict(title=u'{}'.format(ptitle), folder=True, children=[]))
            curpdest = curodest[-1]['children']
            curpsource = curosource[pid]
            for uid in curpsource:
                unum = countu[oid][pid][uid]
                ugood = countu_good[oid][pid][uid]
                uwarn = countu_warn[oid][pid][uid]
                uerr = countu_err[oid][pid][uid]
                utot = countu_tot[uid]
                utitle = title_badge(myid, uid, 'u', None, ugood, uwarn, uerr, unum, utot)
                curpdest.append(dict(title=u'{}'.format(utitle), folder=True, children=[]))
                curudest = curpdest[-1]['children']
                curusource = curpsource[uid]
                for qid in curusource:
                    (qname, qownstatus, qpubstatus, qexestatus) = linfo['q'][qid]
                    rename = u'<a class="{}_{}" lid="{}" href="#"></a>'.format('r' if myid == uid else 'v', 'q', qid)
                    curudest.append(dict(title=u'<a class="q {} {}" n="1" qid="{}" href="#">{}</a> <a class="md" href="#">  <a class="qx {}" href="#"> {}'.format(
                        qownstatus, qpubstatus,
                        qid,
                        #URL('hebrew', 'text', host=True, extension='', vars=dict(iid=qid, page=1, mr='r', qw='q')),
                        h_esc(qname),
                        qexestatus,
                        rename,
                    ), key='q{}'.format(qid), folder=False))
    return dict(data=json.dumps(dest))

tps = dict(o=('organization', 'organization'), p=('project', 'project'), q=('query', 'queries'))

def check_unique(tp, lid, val, myid, msgs):
    result = False
    (label, table) = tps[tp]
    for x in [1]:
        if tp == 'q':
            check_sql = u'''
select id from query where name = '{}' and query.created_by = {};'''.format(val, myid)
        else:
            check_sql = u'''select id from {} where name = '{}';'''.format(table, val)
        try:
            ids = db.executesql(check_sql)
        except:
            msgs.append(('error', u'cannot check the unicity of {} as {}!'.format(val, label)))
            break
        if len(ids) and (lid == 0 or ids[0][0] != int(lid)):
            msgs.append(('error', u'the {} name is already taken!'.format(label)))
            break
        result = True
    return result

def check_name(tp, lid, myid, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 64:
            msgs.append(('error', u'{label} name is longer than 64 characters!'.format(label=label)))
            break
        val = val.strip()
        if val == '':
            msgs.append(('error', u'{label} name consists completely of white space!'.format(label=label)))
            break
        val = val.replace("'","''")
        if not check_unique(tp, lid, val, myid, msgs):
            break
        result = val
    return result

def check_description(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 8192:
            msgs.append(('error', u'{label} description is longer than 8192 characters!'.format(label=label)))
            break
        result = val.replace("'","''")
    return result

def check_mql(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 8192:
            msgs.append(('error', u'{label} mql is longer than 8192 characters!'.format(label=label)))
            break
        result = val.replace("'","''")
    return result

def check_published(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 10 or (len(val) > 0 and not val.isalnum()):
            msgs.append(('error', u'{} published status has an invalid value {}'.format(label, val)))
            break
        result = 'T' if val == 'T' else ''
    return result

def check_website(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 512:
            msgs.append(('error', u'{label} val is longer than 512 characters!'.format(label=label)))
            break
        val = val.strip()
        if val == '':
            msgs.append(('error', u'{label} val consists completely of white space!'.format(label=label)))
            break
        try:
            url_comps = urlparse(val)
        except ValueError:
            msgs.append(('error', u'invalid syntax in {label} website !'.format(label=label)))
            break
        scheme = url_comps.scheme
        if scheme not in {'http', 'https'}:
            msgs.append(('error', u'{label} website does not start with http(s)://'.format(label=label)))
            break
        netloc = url_comps.netloc
        if not '.' in netloc: 
            msgs.append(('error', u'no location in {label} website'.format(label=label)))
            break
        result = urlunparse(url_comps).replace("'","''")
    return result

def check_int(var, label, msgs):
    val = request.vars[var]
    if val == None:
        msgs.append(('error', u'No {} number given'.format(label)))
        return None
    if len(val) > 10 or not val.isdigit():
        msgs.append(('error', u'Not a valid {} verse'.format(label)))
        return None
    return int(val)

def check_id(var, label, msgs):
    val = request.vars[var]
    if val == None:
        msgs.append(('error', u'No {} id given'.format(label)))
        return None
    if len(val) > 10 or not val.isdigit():
        msgs.append(('error', u'Not a valid {} id'.format(label)))
        return None
    return int(val)

def check_rel(tp, val, msgs):
    (label, table) = tps[tp]
    result = None
    for x in [1]:
        check_sql = '''select count(*) as occurs from {} where id = '{}';'''.format(table, val)
        try:
            occurs = db.executesql(check_sql)[0][0]
        except:
            msgs.append(('error', u'cannot check the occurrence of {} id {}!'.format(label, val)))
            break
        if not occurs:
            if val == 0:
                msgs.append(('error', u'No {} chosen!'.format(label)))
            else:
                msgs.append(('error', u'There is no {} {}!'.format(label, val)))
            break
        result = val
    return result

def record():
    msgs = []
    record = {}
    good = False
    myid = auth.user.id if auth.user != None else None
    for x in [1]:
        tp = request.vars.tp
        (label, table) = tps[tp]
        lid = check_id('lid', label, msgs)
        upd = request.vars.upd
        if tp not in tps:
            msgs.append(('error', u'unknown type {}!'.format(tp)))
            break
        if lid == None: break
        if upd not in {'true', 'false'}:
            msgs.append(('error', u'invalid instruction {}!'.format(upd)))
            break
        upd = True if upd == 'true' else False
        if upd and not myid:
            msgs.append(('error', u'for updating you have to be logged in!'))
            break
        fields = ['name']
        if tp == 'q':
            fields.append('organization')
            fields.append('project')
            fields.append('description')
        else:
            fields.append('website')
        if upd:
            (authorized, msg) = query_auth_write(lid) if tp == 'q' else auth_write(label)
        else:
            (authorized, msg) = query_auth_read(lid) if tp == 'q' else auth_write(label)
        if not authorized:
            msgs.append(('error', msg))
            break
        if upd:
            (good, new_lid) = upd_record(tp, lid, myid, fields, msgs)
            if not good:
                break
            lid = new_lid
        else:
            good = True
        if tp == 'q':
            if lid == 0:
                oid = check_id('oid', tps['o'][0], msgs)
                pid = check_id('pid', tps['o'][0], msgs)
                if oid == None or pid == None: break
                osql = u'''select id as oid, name as oname, website as owebsite from organization where id = {};'''.format(oid)
                psql = u'''select id as pid, name as pname, website as pwebsite from project where id = {};'''.format(pid)
                odbrecord = db.executesql(osql, as_dict=True)
                pdbrecord = db.executesql(psql, as_dict=True)
                odbrecord = odbrecord[0] if odbrecord else dict(oid=0, oname='', owebsite='')
                pdbrecord = pdbrecord[0] if pdbrecord else dict(pid=0, pname='', pwebsite='')
                dbrecord = [odbrecord]
                dbrecord[0].update(pdbrecord)
            else: 
                dbrecord = db.executesql(u'''
select
query.id as id,
query.name as name,
query.description as description,
organization.id as oid,
organization.name as oname,
organization.website as owebsite,
project.id as pid,
project.name as pname,
project.website as pwebsite
from query
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
where query.id = {}
'''.format(lid), as_dict=True)
        else:
            if lid == 0:
                pass
            else:
                dbrecord = db.executesql(u'''select {} from {} where id = {}'''.format(','.join(fields), table, lid), as_dict=True)
        if not dbrecord:
            msgs.append(('error', u'No {} with id {}'.format(label, lid)))
            break
        record = dbrecord[0]
        if tp == 'q' and lid != 0:
            record['description_md'] = markdown(record['description'])
    return dict(data=json.dumps(dict(record=record, msgs=msgs, good=good)))

def upd_record(tp, lid, myid, fields, msgs):
    updrecord = {}
    good = False
    (label, table) = tps[tp]
    for x in [1]:
        valsql = check_name(tp, lid, myid, unicode(request.vars.name, encoding='utf-8'), msgs)
        if valsql == None:
            break
        updrecord['name'] = valsql
        if tp == 'q':
            valsql = check_description(tp, unicode(request.vars.description, encoding='utf-8'), msgs)
            if valsql == None:
                break
            updrecord['description'] = valsql
            val = check_id('oid', tps['o'][0], msgs)
            if val == None: break
            valsql = check_rel('o', val, msgs)
            if valsql == None: break
            updrecord['organization'] = valsql
            val = check_id('pid', tps['p'][0], msgs)
            valsql = check_rel('p', val, msgs)
            if valsql == None: break
            updrecord['project'] = valsql
            fld = 'created_' # we only set the modified by and modified on if the query body has been changed
            updrecord[fld+'by'] = myid
            updrecord[fld+'on'] = request.now
            fields.extend([fld+'by', fld+'on'])
        else:
            valsql = check_website(tp, request.vars.website, msgs)
            if valsql == None:
                break
            updrecord['website'] = valsql
        good = True
    if good:
        if lid:
            fieldvals = [u" {} = '{}'".format(f, updrecord[f]) for f in fields]
            sql = u'''update {} set{} where id = {}'''.format(table, ','.join(fieldvals), lid)
            thismsg = 'modified'
        else:
            fieldvals = [u"'{}'".format(updrecord[f]) for f in fields]
            sql = u'''insert into {} ({}) values ({})'''.format(table, u','.join(fields), u','.join(fieldvals), lid)
            thismsg = u'added'
        result = db.executesql(sql)
        if lid == 0:
            lid = db.executesql('select last_insert_id() as x;')[0][0]

        msgs.append((u'good', thismsg))
    return (good, lid)

def windex():
    msgs = []
    good = False
    newwid = None
    for x in [1]:
        oldwid = check_id('oldwid', 'lexicon', msgs)
        if oldwid == None: break
        oldv = request.vars.oldv
        newv = request.vars.newv
        if oldv not in passage_dbs:
            msgs.append(('error', 'No data version {}'.format(oldv)))
            break
        if newv not in passage_dbs:
            msgs.append(('error', 'No data version {}'.format(newv)))
            break
        result = passage_dbs[oldv].executesql('''
select entryid from lexicon where id = {};
'''.format(oldwid)) 
        if result == None or len(result) != 1:
            msgs.append(('error', 'No word with id={} in data version {}'.format(oldwid, oldv)))
            break
        eid = result[0][0]
        eidsql = eid.replace("'", "''").replace('%', '\\%')
        result = passage_dbs[newv].executesql('''
select id from lexicon where entryid = '{}';
'''.format(eidsql)) 
        if result == None or len(result) != 1:
            msgs.append(('error', 'No word entry {} in data version {}'.format(eid, newv)))
            break
        newwid = result[0][0]
        good = True
        msgs.append(('special', '{} in {} is {} is {} in {}'.format(oldwid, oldv, h_esc(eid), newwid, newv)))
    return dict(data=json.dumps(dict(msgs=msgs, good=good, newwid=newwid)))

def field():
    msgs = []
    good = False
    mod_date_fld = None
    mod_dates = {}
    extra = {}
    myid = auth.user.id if auth.user != None else None
    for x in [1]:
        qid = check_id('qid', 'query', msgs)
        if qid == None: break
        fname = request.vars.fname
        val = request.vars.val
        vr = request.vars.version
        if fname == None or fname not in {'is_shared', 'is_published'}:
            msgs.append('error', 'Illegal field name {}')
            break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(('error', msg))
            break
        (good, mod_dates, mod_cls, extra) = upd_field(vr, qid, fname, val, msgs)
    return dict(data=json.dumps(dict(msgs=msgs, good=good, mod_dates=mod_dates, mod_cls=mod_cls, extra=extra)))

def upd_shared(myid, qid, valsql, msgs):
    mod_date = None
    mod_date_fld = 'shared_on'
    good = False
    table = 'query'
    fname = 'is_shared'
    ckeys = r'^items_q_'
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    fieldval = u" {} = '{}'".format(fname, valsql)
    mod_date = request.now.replace(microsecond=0) if valsql == 'T' else None
    mod_date_sql = 'null' if mod_date == None else "'{}'".format(mod_date)
    fieldval += u", {} = {} ".format(mod_date_fld, mod_date_sql) 
    sql = u"update {} set{} where id = {}".format(table, fieldval, qid)
    result = db.executesql(sql)
    thismsg = 'modified'
    thismsg = 'shared' if valsql == 'T' else 'UNshared'
    msgs.append((u'good', thismsg))
    return (mod_date_fld, str(mod_date) if mod_date else NULLDT)

def upd_published(myid, vr, qid, valsql, msgs):
    mod_date = None
    mod_date_fld = 'published_on'
    good = False
    table = 'query_exe'
    fname = 'is_published'
    ckeys = r'^items_q_{}_'.format(vr)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    verify_version(qid, vr)
    fieldval = u" {} = '{}'".format(fname, valsql)
    mod_date = request.now.replace(microsecond=0) if valsql == 'T' else None
    mod_date_sql = 'null' if mod_date == None else "'{}'".format(mod_date)
    fieldval += u", {} = {} ".format(mod_date_fld, mod_date_sql) 
    sql = u"update {} set{} where query_id = {} and version = '{}'".format(table, fieldval, qid, vr)
    result = db.executesql(sql)
    thismsg = 'modified'
    thismsg = 'published' if valsql == 'T' else 'UNpublished'
    msgs.append((u'good', thismsg))
    return (mod_date_fld, str(mod_date) if mod_date else NULLDT)

def upd_field(vr, qid, fname, val, msgs):
    good = False
    myid = None
    mod_dates = {}
    mod_cls = {}
    extra = {}
    if auth.user:
        myid = auth.user.id
    for x in [1]:
        valsql = check_published('q', unicode(val, encoding='utf-8'), msgs)
        if valsql == None:
            break
        if fname == 'is_shared' and valsql == '':
            sql = '''select count(*) from query_exe where query_id = {} and is_published = 'T';'''.format(qid)
            pv = db.executesql(sql)
            has_public_versions = pv != None and len(pv) == 1 and pv[0][0] > 0
            if has_public_versions:
                msgs.append(('error', 'You cannot UNshare this query because there is a published execution record'))
                break
        if fname == 'is_published':
            mod_cls['is_pub_ro'] = 'fa-{}'.format('check' if valsql == 'T' else 'close')
            extra['execq'] = ('show', valsql != 'T')
            if valsql == 'T':
                sql = '''select executed_on, modified_on as xmodified_on from query_exe where query_id = {} and version = '{}';'''.format(qid, vr)
                pv = db.executesql(sql, as_dict=True)
                if pv == None or len(pv) != 1:
                    msgs.append(('error', 'cannot determine whether query results are up to date'))
                    break
                uptodate = qstatus(pv[0])
                if uptodate != 'good':
                    msgs.append(('error', 'You can only publish if the query results are up to date'))
                    break
                sql = '''select is_shared from query where id = {};'''.format(qid)
                pv = db.executesql(sql)
                is_shared = pv != None and len(pv) == 1 and pv[0][0] == 'T'
                if not is_shared:
                    (mod_date_fld, mod_date) = upd_shared(myid, qid, 'T', msgs)
                    mod_dates[mod_date_fld] = mod_date
                    extra['is_shared'] = ('checked', True)
            else:
                sql = '''select published_on from query_exe where query_id = {} and version = '{}';'''.format(qid, vr)
                pv = db.executesql(sql)
                pdate_ok = pv == None or len(pv) != 1 or pv[0][0] > request.now - PUBLISH_FREEZE
                if not pdate_ok:
                    msgs.append(('error', 'You cannot UNpublish this query because it has been published more than {} ago'.format(PUBLISH_FREEZE_MSG)))
                    break

        good = True

    if good:
        if fname == 'is_shared':
            (mod_date_fld, mod_date) = upd_shared(myid, qid, valsql, msgs)
        else:
            (mod_date_fld, mod_date) = upd_published(myid, vr, qid, valsql, msgs)
        mod_dates[mod_date_fld] = mod_date
    return (good, mod_dates, mod_cls, extra)

def verify_version(qid, vr):
    exist_version = db.executesql('''
select id from query_exe where version = '{}' and query_id = {};
'''.format(vr, qid))
    if exist_version == None or len(exist_version) == 0:
        db.executesql('''
insert into query_exe (id, version, query_id) values (null, '{}', {});
'''.format(vr, qid))

def fields():
    msgs = []
    good = False
    updrecord = {}
    label = 'query'
    myid = auth.user.id if auth.user != None else None
    flds = {}
    fldx = {}
    vr = request.vars.version
    q_record = {}
    for x in [1]:
        qid = check_id('qid', 'query', msgs)
        if qid == None: break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(('error', msg))
            break
        
        verify_version(qid, vr)
        oldrecord = db.executesql('''
select
    query.name as name,
    query.description as description,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{}'
where query.id = {};
'''.format(vr, qid), as_dict=True)
        if oldrecord == None or len(oldrecord) == 0:
            msgs.append(('error', 'No query with id {}'.format(qid)))
            break
        oldvals = oldrecord[0]
        is_published = oldvals['is_published'] == 'T'
        if not is_published:
            newname = unicode(request.vars.name, encoding='utf-8')
            if oldvals['name'] != newname:
                valsql = check_name('q', qid, myid, newname, msgs)
                if valsql == None:
                    break
                flds['name'] = valsql
                flds['modified_on'] = request.now
            newmql = request.vars.mql
            if oldvals['mql'] != newmql:
                msgs.append(('warning', 'query body modified'))
                valsql = check_mql('q', unicode(newmql, encoding='utf-8'), msgs)
                if valsql == None:
                    break
                fldx['mql'] = valsql
                fldx['modified_on'] = request.now
            else:
                msgs.append(('good', 'same query body'))
        else:
            msgs.append(('warning', 'only the description can been saved because this is a published query execution'))
        newdesc = unicode(request.vars.description, encoding='utf-8')
        if oldvals['description'] != newdesc:
            valsql = check_description('q', newdesc, msgs)
            if valsql == None:
                break
            flds['description'] = valsql
            flds['modified_on'] = request.now
        good = True
    if good:
        execute = request.vars.execute
        xgood = True
        if execute == 'true':
            (xgood, xresults) = mql(vr, newmql) 
            if xgood:
                store_monad_sets(vr, qid, xresults)
                fldx['executed_on'] = request.now
                msgs.append(('good', 'Query executed'))
            else:
                store_monad_sets(vr, qid, [])
                msgs.append(('error', u'<code class="merr">{}</code>'.format(xresults)))
        if len(flds):
            sql = u"update {} set{} where id = {}".format(
                'query',
                ', '.join(u" {} = '{}'".format(f, flds[f]) for f in flds if f != 'status'),
                qid,
            )
            db.executesql(sql)
            ckeys = r'^items_q_'
            cache.ram.clear(regex=ckeys)
            cache.disk.clear(regex=ckeys)
        if len(fldx):
            sql = u"update {} set{} where query_id = {} and version = '{}'".format(
                'query_exe',
                ', '.join(u" {} = '{}'".format(f, fldx[f]) for f in fldx if f != 'status'),
                qid,
                vr,
            )
            db.executesql(sql)
            ckeys = r'^items_q_{}_'.format(vr)
            cache.ram.clear(regex=ckeys)
            cache.disk.clear(regex=ckeys)
        sql = u'''select name, description, modified_on from query where id = {};'''.format(qid)
        records = db.executesql(sql, as_dict=True)
        if records == None or len(records) == 0:
            msgs.append(('error', 'No query with id {}'.format(qid)))
            good = False
        else:
            q_record = records[0]
            q_record['description_md'] = markdown(q_record['description'])
            for f in ('modified_on',):
                q_record[f] = str(q_record[f])
            sql = '''
select
    mql,
    version,
    resultmonads,
    results,
    executed_on,
    modified_on as xmodified_on
from query_exe
where query_id = {}
'''.format(qid)
            recordx = db.executesql(sql, as_dict=True)
            query_fields(vr, q_record, recordx, single_version=False)

    return dict(data=json.dumps(dict(msgs=msgs, good=good and xgood, q=q_record)))

def datetime_str(fields):
    for f in ('created_on', 'modified_on', 'shared_on', 'xmodified_on', 'executed_on', 'published_on'):
        if f in fields:
            ov = fields[f]
            fields[f] = str(ov) if ov else NULLDT
    for f in ('is_shared', 'is_published'):
        if f in fields: fields[f] = fields[f] == 'T'

def qstatus(qx_record):
    if not qx_record['executed_on']:
        return 'warning'
    if qx_record['executed_on'] < qx_record['xmodified_on']:
        return 'error'
    return 'good'

def query_fields(vr, q_record, recordx, single_version=False):
    datetime_str(q_record)
    if not single_version:
        q_record['versions'] = dict((v, dict(
            xid=None,
            mql=None,
            status='warning',
            is_published=None,
            results=None,
            resultmonads=None,
            xmodified_on=None,
            executed_on=None,
            published_on=None,
        )) for v in versions if versions[v]['date'])
        for rx in recordx:
            vx = rx['version']
            dest = q_record['versions'][vx]
            dest.update(rx)
            dest['status'] = qstatus(dest)
            datetime_str(dest)

def get_query_info(iid, vr, msgs, single_version=False, with_ids=True, po=False):
    sqli = ''',
    query.created_by as uid,
    project.id as pid,
    organization.id as oid
''' if with_ids and po else ''

    sqlx = ''',
    query_exe.id as xid,
    query_exe.mql as mql,
    query_exe.version as version,
    query_exe.resultmonads as resultmonads,
    query_exe.results as results,
    query_exe.executed_on as executed_on,
    query_exe.modified_on as xmodified_on,
    query_exe.is_published as is_published,
    query_exe.published_on as published_on
''' if single_version else ''

    sqlp = ''',
    project.name as pname,
    project.website as pwebsite,
    organization.name as oname,
    organization.website as owebsite
''' if po else ''

    sqlm = '''
    query.id as id,
    query.name as name,
    query.description as description,
    query.created_on as created_on,
    query.modified_on as modified_on,
    query.is_shared as is_shared,
    query.shared_on as shared_on,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    auth_user.email as uemail
    {}{}{}
'''.format(sqli, sqlp, sqlx)

    sqlr = '''
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{}'
'''.format(vr) if single_version else ''

    sqlpr = '''
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
''' if po else ''

    sqlc = '''
where query.id in ({})
'''.format(','.join(iid)) if single_version else '''
where query.id = {}
'''.format(iid)

    sqlo = '''
order by auth_user.last_name, query.name
''' if single_version else ''

    sql = '''
select{}
from query
inner join auth_user on query.created_by = auth_user.id
{}{}{}{}
'''.format(sqlm, sqlr, sqlpr, sqlc, sqlo)
    records = db.executesql(sql, as_dict=True)
    if records == None:
        msgs.append(('error', 'Cannot lookup query(ies)'))
        return None
    if single_version:
        for q_record in records:
            query_fields(vr, q_record, [], single_version=True)
        return records
    else:
        if len(records) == 0:
            msgs.append(('error', 'No query with id {}'.format(iid)))
            return None
        q_record = records[0]
        q_record['description_md'] = markdown(q_record['description'])
        sql = '''
select
    id as xid,
    mql,
    version,
    resultmonads,
    results,
    executed_on,
    modified_on as xmodified_on,
    is_published,
    published_on
from query_exe
where query_id = {}
'''.format(iid)
        recordx = db.executesql(sql, as_dict=True)
        query_fields(vr, q_record, recordx, single_version=False)
        return q_record

def sideq():
    session.forget(response)
    msgs = []
    iid = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (authorized, msg) = query_auth_read(iid)
    if not authorized or not iid:
        msgs.append(('error', msg))
        return dict(
            writable=False,
            iid = iid,
            vr = vr,
            qr = {},
            q=collections.defaultdict(lambda: ''),
            msgs=json.dumps(msgs),
        )
    q_record = get_query_info(iid, vr, msgs, with_ids=True, single_version=False, po=True)
    if q_record == None:
        return dict(
            writable=True,
            iid = iid,
            vr = vr,
            qr = {},
            q=collections.defaultdict(lambda: ''),
            msgs=json.dumps(msgs),
        )

    (authorized, msg) = query_auth_write(iid=iid)

    return dict(
        writable=authorized,
        iid = iid,
        vr = vr,
        qr = q_record,
        q=json.dumps(q_record),
        msgs=json.dumps(msgs),
    )

def sidew():
    session.forget(response)
    msgs = []
    vr = get_request_val('material', '', 'version')
    iid = get_request_val('material', '', 'iid')
    (authorized, msg) = word_auth_read(vr, iid)
    if not authorized or not iid:
        msgs.append(('error', msg))
        return dict(
            w=collections.defaultdict(lambda: ''),
            msgs=json.dumps(msgs),
        )
    sql = '''
select *
from lexicon
where lexicon.id = {}
'''.format(iid)
    records = passage_dbs[vr].executesql(sql, as_dict=True)
    if records == None or len(records) == 0:
        msgs.append(('error', 'No word with id {}'.format(iid)))
        return dict(
            w=collections.defaultdict(lambda: ''),
            msgs=json.dumps(msgs),
        )
    word = records[0]

    return dict(
        w=json.dumps(word),
        msgs=json.dumps(msgs),
    )

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
            result.add(m)
    return list(sorted(result))

def getpassage(no_controller=True):
    vr = get_request_val('material', '', 'version')
    bookname = get_request_val('material', '', 'book')
    chapternum = get_request_val('material', '', 'chapter')
    if bookname == None or chapternum == None: return ({},{})
    bookrecords = passage_dbs[vr].executesql('''select * from book where name = '{}';'''.format(bookname), as_dict=True)
    book = bookrecords[0] if bookrecords else {}
    chapterrecords = passage_dbs[vr].executesql('''select * from chapter where chapter_num = {} and book_id = {};'''.format(chapternum, book['id']), as_dict=True)
    chapter = chapterrecords[0] if chapterrecords else {}
    return (book, chapter)

def groupq(vr, input):
    monads = collections.defaultdict(lambda: set())
    for (qid, b, e) in input:
        monads[qid] |= set(range(b, e + 1))
    r = []
    if len(monads):
        msgs = []
        queryrecords = get_query_info((str(q) for q in monads), vr, msgs, with_ids=False, single_version=True, po=False)
        for q in queryrecords:
            r.append({'item': q, 'monads': json.dumps(sorted(list(monads[q['id']])))})
    return r

def groupw(vr, input):
    wids = collections.defaultdict(lambda: [])
    for x in input:
        wids[x[1]].append(x[0])
    r = []
    if len(wids):
        wsql = '''
select * from lexicon
where
    id in ({})
order by entryid_heb
'''.format(','.join(str(x) for x in wids))
        wordrecords = passage_dbs[vr].executesql(wsql, as_dict=True)
        for w in wordrecords:
            r.append({'item': w, 'monads': json.dumps(wids[w['id']])})
    return r

def get_monads(vr, chapter, pub):
    if pub == 'x':
        pubv = ""
        pubx = "inner join query on query.id = query_exe.query_id and query.is_shared = 'T'"
    else:
        pubv = " and query_exe.is_published = 'T'"
        pubx = ""
    return db.executesql(u'''
select DISTINCT
    query_exe.query_id as query_id,
    GREATEST(first_m, {chapter_first_m}) as first_m,
    LEAST(last_m, {chapter_last_m}) as last_m
from
    monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and query_exe.executed_on >= query_exe.modified_on {pubv}
{pubx}
where
    (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    ({chapter_first_m} BETWEEN first_m AND last_m);
'''.format(
         chapter_last_m=chapter['last_m'],
         chapter_first_m=chapter['first_m'],
         vr=vr,
         pubv=pubv,
         pubx=pubx,
    ))

def get_lexemes(vr, chapter):
    return passage_dbs[vr].executesql(u'''
select
    anchor, lexicon_id
from
    word_verse
where
    anchor BETWEEN {chapter_first_m} AND {chapter_last_m}
'''.format(
         chapter_last_m=chapter['last_m'],
         chapter_first_m=chapter['first_m'],
    ))

def query_access_read(iid=get_request_val('material', '', 'iid')):
    if get_request_val('material', '', 'mr') == 'm' or get_request_val('material', '', 'qw') == 'w':
       return (True, '')
    if iid != None and iid > 0:
        return query_auth_read(iid)
    return (None, u'Not a valid id {}'.format(iid))

def query_auth_read(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user != None
    else:
        q_records = db.executesql('select * from query where id = {};'.format(iid), as_dict=True)
        q_record = q_records[0] if q_records else {}
        if q_record:
            authorized = q_record['is_shared'] or (auth.user != None and q_record['created_by'] == auth.user.id)
    msg = u'No query with id {}'.format(iid) if authorized == None else u'You have no access to item with id {}'.format(iid) 
    return (authorized, msg)

def word_auth_read(vr, iid):
    authorized = None
    if iid == 0:
        authorized = auth.user != None
    else:
        words = passage_dbs[vr].executesql('select * from lexicon where id = {};'.format(iid), as_dict=True)
        word = words[0] if words else {}
        if word:
            authorized = True
    msg = u'No word with id {}'.format(iid) if authorized == None else u''
    return (authorized, msg)

def query_auth_write(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user != None
    else:
        q_records = db.executesql('select * from query where id = {};'.format(iid), as_dict=True)
        q_record = q_records[0] if q_records else {}
        if q_record != None:
            authorized = (auth.user != None and q_record['created_by'] == auth.user.id)
    msg = u'No item with id {}'.format(iid) if authorized == None else u'You have no access to create/modify item with id {}'.format(iid) 
    return (authorized, msg)

@auth.requires_login()
def auth_write(label):
    authorized = auth.user != None
    msg = u'You have no access to create/modify a {}'.format(label) 
    return (authorized, msg)

def get_qx(vr, iid):
    recordx = db.executesql("select id from query_exe where query_id = {} and version = '{}';".format(iid, vr))
    if recordx == None or len(recordx) != 1: return None
    return recordx[0][0]

def store_monad_sets(vr, iid, rows):
    xid = get_qx(vr, iid)
    if xid == None: return
    db.executesql("delete from monads where query_exe_id={};".format(xid))
    # Here we clear stuff that will become invalid because of a (re)execution of a query
    # and the deleting of previous results and the storing of new results.
    ckeys = r'^verses_{}_q_{}_'.format(vr, iid)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    ckeys = r'^items_q_{}_'.format(vr)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    ckeys = r'^chart_{}_q_{}_'.format(vr, iid)
    cache.ram.clear(regex=ckeys)
    cache.disk.clear(regex=ckeys)
    nrows = len(rows)
    if nrows == 0: return

    limit_row = 10000
    start = '''
insert into monads (query_exe_id, first_m, last_m) values
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
        query += '({},{},{})'.format(xid, row[0], row[1])
        if r + 1 < nrows:
            for row in rows[r + 1:s]: 
                query += ',({},{},{})'.format(xid, row[0], row[1])
        r = s
    if query != '':
        db.executesql(query)
        query = ''

def load_monad_sets(vr, iid):
    xid = get_qx(vr, iid)
    if xid == None: return normalize_ranges([])
    monad_sets = db.executesql('''
select first_m, last_m from monads where query_exe_id = {} order by first_m;
'''.format(xid))
    return normalize_ranges(monad_sets)

def load_word_occurrences(vr, lexeme_id):
    monads = passage_dbs[vr].executesql('SELECT anchor FROM word_verse WHERE lexicon_id = {} ORDER BY anchor;'.format(lexeme_id))
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

def get_pagination(vr, p, monad_sets, iid):
    verse_boundaries = from_cache(
        'verse_boundaries_{}_'.format(vr),
        lambda: passage_dbs[vr].executesql('SELECT first_m, last_m FROM verse ORDER BY id;'),
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

def get_chart(vr, monad_sets): # get data for a chart of the monadset: organized by book and block
# return a dict keyed by book, with values lists of blocks 
# (chapter num, start point, end point, number of results, size)

    monads = flatten(monad_sets)
    data = []
    chart = {}
    chart_order = []
    if len(monads):
        (books, books_order) = from_cache('books_{}_'.format(vr), lambda: get_books(vr), None)
        (blocks, block_mapping) = from_cache('blocks_{}_'.format(vr), lambda: get_blocks(vr), None)
        results = {}

        for bl in range(len(blocks)):
            results[bl] = 0
        for bk in books_order:
            chart[bk] = []
            chart_order.append(bk)
        for m in monads:
            results[block_mapping[m]] += 1
        for bl in range(len(blocks)):
            (bk, ch_start, ch_end, size) = blocks[bl]
            r = results[bl]
            chart[bk].append((ch_start[0], ch_start[1], ch_end[1], r, size))

    return dict(chart=json.dumps(chart), chart_order=json.dumps(chart_order))

