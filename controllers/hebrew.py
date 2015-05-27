#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)
import collections, json, datetime, re
from urlparse import urlparse, urlunparse
from markdown import markdown

from render import Verses, Verse, Viewsettings, legend, colorpicker, h_esc, get_request_val, get_fields, style, tp_labels, tab_views, iid_encode, iid_decode
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
# verses_{vr}_{mqw}_{bk/iid}_{ch/page}_{tp}_    verses on a material page, either for a chapter,
#                                                    or an occurrences page of a lexeme,
#                                                    or a results page of a query execution
#                                                    or a page with notes by a user with a keyword
# verse_{vr}_{bk}_{ch}_{vs}_                    a single verse in data representation
# items_{qw}_{vr}_{bk}_{ch}_{pub}_              the items (queries or words) in a sidebar list of a page that shows a chapter
# chart_{vr}_{qw}_{iid}_                        the chart data for a query or word
# words_page_{vr}_{lan}_{letter}_               the data for a word index page
# words_data_{vr}_                              the data for the main word index page


RESULT_PAGE_SIZE = 20
BLOCK_SIZE = 500
PUBLISH_FREEZE = datetime.timedelta(weeks=1)
PUBLISH_FREEZE_MSG = u'1 week'
NULLDT = u'____-__-__ __:__:__'

CACHING = True
CACHING_RAM_ONLY = True

WORD_PAT = re.compile(ur'[^\s]+', re.UNICODE)

def from_cache(ckey, func, expire):
    if CACHING:
        if CACHING_RAM_ONLY:
            result = cache.ram(ckey, func, time_expire=expire)
        else:
            result = cache.ram(ckey, lambda:cache.disk(ckey, func, time_expire=expire), time_expire=expire)
    else:
        result = func()
    return result

def clear_cache(ckeys):
    cache.ram.clear(regex=ckeys)
    if not CACHING_RAM_ONLY:
        cache.disk.clear(regex=ckeys)

def text():
    session.forget(response)
    books = {}
    books_order = {}
    book_id = {}
    book_name = {}
    for vr in versions:
        if not versions[vr]['date']: continue
        (books[vr], books_order[vr], book_id[vr], book_name[vr]) = from_cache('books_{}_'.format(vr), lambda:get_books(vr), None)

    return dict(
        viewsettings=Viewsettings(versions),
        versions=versions,
        colorpicker=colorpicker,
        legend=legend,
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
        tp_labels=tp_labels,
        tab_views=tab_views,
    )

def get_clause_atom_fmonad(vr):
    (books, books_order, book_id, book_name) = from_cache('books_{}_'.format(vr), lambda: get_books(vr), None)
    sql = u'''
select book_id, ca_num, first_m
from clause_atom 
;
'''
    ca_data = passage_dbs[vr].executesql(sql)
    clause_atom_first = {}
    for (bid, can, fm) in ca_data:
        bnm = book_name[bid]
        clause_atom_first.setdefault(bnm, {})[can] = fm
    return clause_atom_first

def get_clause_atoms(vr, bk, ch, vs): # get clauseatoms for each verse
    clause_atoms = {}
    ca_data = passage_dbs[vr].executesql(u'''
select
   distinct word.clause_atom_number
from 
    verse
inner join 
    word_verse on verse.id = word_verse.verse_id
inner join
    word on word.word_number = word_verse.anchor
inner join
    chapter on chapter.id = verse.chapter_id
inner join
    book on book.id = chapter.book_id
where
    book.name = '{}' and chapter.chapter_num = {} and verse.verse_num = {}
order by
    word.clause_atom_number
;
'''.format(bk, ch, vs))

    for (can,) in ca_data:
        clause_atoms.setdefault((bk, ch, vs), []).append(can)
    return clause_atoms

#def get_sections(vr): # get the list of verse numbers per chapter
#    records = passage_dbs[vr].executesql(u'''
#select
#    book.name, chapter.chapter_num, verse.verse_num
#from book
#inner join chapter on book.id = chapter.book_id
#inner join verse on chapter.id = verse.chapter_id
#order by verse.versenum
#;
#''')
#    sections = {}
#    for (b, c, v) in records:
#        sections.setdefault(b, {}).setdefault(c, []).append(v)
#    return sections

def get_books(vr): # get book information: number of chapters per book
    books_data = passage_dbs[vr].executesql(u'''
select book.id, book.name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id
;
''')
    books_order = [x[1] for x in books_data]
    books = dict((x[1], x[2]) for x in books_data)
    book_id = dict((x[1], x[0]) for x in books_data)
    book_name = dict((x[0], x[1]) for x in books_data)
    return (books, books_order, book_id, book_name)

def get_blocks(vr): # get block info: for each monad: to which block it belongs, for each block: book and chapter number of first word.
# possibly there are gaps between books.
    book_monads = passage_dbs[vr].executesql(u'''
select name, first_m, last_m from book
;
''')
    chapter_monads = passage_dbs[vr].executesql(u'''
select chapter_num, first_m, last_m from chapter
;
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
        rep = u'{}.Z'.format(cur_ch) if n == cur_ch_l else u'{}.z'.format(cur_ch) if round(10* fraction) == 10 else u'{:0.1f}'.format(cur_ch+fraction)
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
    return (blocks, block_mapping)

def material():
    session.forget(response)
    mr = get_request_val('material', '', 'mr')
    qw = get_request_val('material', '', 'qw')
    vr = get_request_val('material', '', 'version')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    tp = get_request_val('material', '', 'tp')
    iidrep = get_request_val('material', '', 'iid')
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        return dict(
            version=vr,
            mr=mr,
            qw=qw,
            msg=msg,
            hits=0,
            results=0,
            pages=0,
            page=0,
            pagelist=json.dumps([]),
            material=None,
            monads=json.dumps([]),
        )
    page = get_request_val('material', '', 'page')
    mrrep = 'm' if mr == 'm' else qw
    return from_cache(
        'verses_{}_{}_{}_{}_{}_'.format(vr, mrrep, bk if mr=='m' else iidrep, ch if mr=='m' else page, tp),
        lambda: material_c(vr, mr, qw, bk, iidrep, ch, page, tp),
        None,
    )

def material_c(vr, mr, qw, bk, iidrep, ch, page, tp):
    if mr == 'm':
        (book, chapter) = getpassage()
        material = Verses(passage_dbs, vr, mr, chapter=chapter['id'], tp=tp) if chapter else None
        result = dict(
            mr=mr,
            qw=qw,
            hits=0,
            msg=u'{} {} does not exist'.format(bk, ch) if not chapter else None,
            results=len(material.verses) if material else 0,
            pages=1,
            material=material,
            monads=json.dumps([]),
        )
    elif mr == 'r':
        (iid, kw) = (None, None)
        if iidrep != None: (iid, kw) = iid_decode(qw, iidrep)
        if iid == None:
            msg = u'No {} selected'.format('query' if qw == 'q' else u'word' if qw == 'w' else u'note set')
            result = dict(
                mr=mr,
                qw=qw,
                msg=msg,
                hits=0,
                results=0,
                pages=0,
                page=0,
                pagelist=json.dumps([]),
                material=None,
                monads=json.dumps([]),
            )
        else:
            (nmonads, monad_sets) = load_q_hits(vr, iid) if qw == 'q' else load_w_occs(vr, iid) if qw == 'w' else load_n_notes(vr, iid, kw)
            (nresults, npages, verses, monads) = get_pagination(vr, page, monad_sets)
            material = Verses(passage_dbs, vr, mr, verses, tp=tp)
            result = dict(
                mr=mr,
                qw=qw,
                msg=None,
                hits=nmonads,
                results=nresults,
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
        msgs.append(('error', u'{} {}:{} does not exist'.format(bk, ch, vs)))
        good = False
    result = dict(
        good = good,
        msgs = msgs,
        material=material,
    )
    return result

def cnotes():
    myid = None
    msgs = []
    if auth.user:
        myid = auth.user.id
    vr = get_request_val('material', '', 'version')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    vs = check_int('verse', 'verse', msgs)
    if vs == None:
        return json.dumps(dict(good=False, msgs=msgs, users={}, notes={}))
    save = request.vars.save
    clause_atoms = from_cache('clause_atoms_{}_{}_{}_{}_'.format(vr, bk, ch, vs), lambda: get_clause_atoms(vr, bk, ch, vs), None)
    these_clause_atoms = clause_atoms[(bk, ch, vs)]
    changed = False
    if save == 'true':
        changed = note_save(myid, vr, bk, ch, vs, these_clause_atoms, msgs)
    return cnotes_c(vr, bk, ch, vs, myid, these_clause_atoms, changed, msgs)

def key_add(kw, nid):
    insert_sql = u'''
insert into key_note (keyword, note_id) values {}
;
'''.format(
        u','.join(u"('{}', {})".format(k, nid) for k in {x.lower() for x in WORD_PAT.findall(kw)}),
    )
    note_db.executesql(insert_sql)

def key_del(nids):
    del_sql = u'''
delete from key_note where note_id in ({})
;
'''.format(u','.join(str(nid) for nid in nids))
    note_db.executesql(del_sql)

def note_save(myid, vr, bk, ch, vs, these_clause_atoms, msgs):
    if myid == None:
        msgs.append(('error', u'You have to be logged in when you save notes'))
        return
    notes = json.loads(request.post_vars.notes)
    (good, old_notes, upd_notes, new_notes, del_notes) = note_filter_notes(myid, notes, these_clause_atoms, msgs)

    updated = 0
    for nid in upd_notes:
        (shared, pub, stat, kw, ntxt) = upd_notes[nid]
        (o_shared, o_pub, o_stat, o_kw, o_ntxt) = old_notes[nid]
        extrafields = []
        if shared and not o_shared:
            extrafields.append(u",\n\tshared_on = '{}'".format(request.now)) 
        if not shared and o_shared:
            extrafields.append(u',\n\tshared_on = null') 
        if pub and not o_pub:
            extrafields.append(u",\n\tpublished_on = '{}'".format(request.now)) 
        if not pub and o_pub:
            extrafields.append(u',\n\tpublished_on = null') 
        shared = "'T'" if shared else 'null'
        pub = "'T'" if pub else 'null'
        stat = 'o' if stat not in {'o', '*', '+', '?', '-', '!'} else stat
        if o_kw != kw: key_del([nid])
        update_sql = u'''
update note set modified_on = '{}', is_shared = {}, is_published = {}, status = '{}', keywords = '{}', ntext = '{}'{}
where id = {}
; 
'''.format(request.now, shared, pub, stat, kw.replace(u"'",u"''"), ntxt.replace(u"'",u"''"), u''.join(extrafields), nid)
        note_db.executesql(update_sql)
        if o_kw != kw: key_add(kw, nid)
        updated += 1
    if len(del_notes) > 0:
        key_del(del_notes)
        del_sql = u'''
delete from note where id in ({})
;
'''.format(u','.join(str(x) for x in del_notes))
        note_db.executesql(del_sql)
    for canr in new_notes:
        (shared, pub, stat, kw, ntxt) = new_notes[canr]
        insert_sql = u'''
insert into note
(version, book, chapter, verse, clause_atom, created_by, created_on, modified_on, is_shared, shared_on, is_published, published_on, status, keywords, ntext)
values
('{}', '{}', {}, {}, {}, {}, '{}', '{}', {}, {}, {}, {}, '{}', '{}', '{}')
;
'''.format(
    vr, bk, ch, vs, canr, myid, request.now, request.now,
    "'T'" if shared else 'null',
    u"'{}'".format(request.now) if shared else 'null',
    "'T'" if pub else 'null',
    u"'{}'".format(request.now) if pub else 'null',
    'o' if stat not in {'o', '*', '+', '?', '-', '!'} else stat,
    kw.replace(u"'",u"''"),
    ntxt.replace(u"'",u"''"),
)
        note_db.executesql(insert_sql)
        nid = note_db.executesql(u'''
select last_insert_id() as x
;
''')[0][0]
        key_add(kw, nid)

    changed = False
    if len(del_notes) > 0:
        msgs.append(('special', u'Deleted notes: {}'.format(len(del_notes))))
    if updated > 0:
        msgs.append(('special', u'Updated notes: {}'.format(updated)))
    if len(new_notes) > 0:
        msgs.append(('special', u'Added notes: {}'.format(len(new_notes))))
    if len(del_notes) + len(new_notes) + updated == 0:
        msgs.append(('warning', u'No changes'))
    else:
        changed = True
        clear_cache(r'^items_n_{}_{}_{}_'.format(vr, bk, ch))
        clear_cache(r'^verses_{}_{}_{}_'.format(vr, 'n', iid_encode('n', myid, kw=kw)))
    return changed

def note_filter_notes(myid, notes, these_clause_atoms, msgs):
    good = True
    other_user_notes = set()
    missing_notes = set()
    extra_notes = set()
    same_notes = set()
    clause_errors = set()
    emptynew = 0
    old_notes = {}
    upd_notes = {}
    new_notes = {}
    del_notes = set()
    for fields in notes:
        nid = int(fields['nid'])
        uid = int(fields['uid'])
        canr = int(fields['canr'])
        if uid != myid:
            other_user_notes.add(nid)
            good = False
            continue
        if canr not in these_clause_atoms:
            clause_errors.add(nid)
            good = False
            continue
        kw = fields['kw'].strip()
        ntxt = fields['ntxt'].strip()
        if kw == u'' and ntxt == u'':
            if nid == 0:
                emptynew += 1
            else:
                del_notes.add(nid)
            continue
        if nid != 0:
            upd_notes[nid] = (fields['shared'], fields['pub'], fields['stat'], kw, ntxt)
        else:
            new_notes[fields['canr']] = (fields['shared'], fields['pub'], fields['stat'], kw, ntxt)
    if len(upd_notes) > 0 or len(del_notes) > 0:
        old_sql = u'''
select id, created_by, is_shared, is_published, status, keywords, ntext
from note where id in ({})
;
'''.format(u','.join(str(x) for x in (set(upd_notes.keys()) | del_notes)))
        cresult = note_db.executesql(old_sql)
        if cresult != None:
            for (nid, uid, o_shared, o_pub, o_stat, o_kw, o_ntxt) in cresult:
                remove = False
                if uid != myid:
                    other_user_notes.add(nid)
                    remove = True
                elif nid not in upd_notes and nid not in del_notes:
                    extra_notes.add(nid)
                    remove = True
                elif nid in upd_notes:
                    (shared, pub, stat, kw, ntxt) = upd_notes[nid]
                    if not shared: shared = None
                    if not pub: pub = None
                    if o_stat == stat and o_kw == kw and o_ntxt == ntxt and o_shared == shared and o_pub == pub:
                        same_notes.add(nid)
                        if nid not in del_notes:
                            remove = True
                if remove:
                    if nid in upd_notes: del upd_notes[nid]
                    if nid in del_notes: del_notes.remove(nid)
                else:
                    old_notes[nid] = (o_shared, o_pub, o_stat, o_kw, o_ntxt) 
    to_remove = set()
    for nid in upd_notes:
        if nid not in old_notes:
            if nid not in other_user_notes:
                missing_notes.add(nid)
                to_remove.add(nid)
    for nid in to_remove:
        del upd_notes[nid]
    to_remove = set()
    for nid in del_notes:
        if nid not in old_notes:
            if nid not in other_user_notes:
                missing_notes.add(nid)
                to_remove.add(nid)
    for nid in to_remove:
        del_notes.remove(nid)
    if len(other_user_notes) > 0:
        msgs.append(('error', u'Notes of other users skipped: {}'.format(len(other_user_notes))))
    if len(missing_notes) > 0:
        msgs.append(('error', u'Non-existing notes: {}'.format(len(missing_notes))))
    if len(extra_notes) > 0:
        msgs.append(('error', u'Notes not shown: {}'.format(len(extra_notes))))
    if len(clause_errors) > 0:
        msgs.append(('error', u'Notes referring to wrong clause: {}'.format(len(clause_errors))))
    if len(same_notes) > 0:
        pass
        #msgs.append(('info', u'Unchanged notes: {}'.format(len(same_notes))))
    if emptynew > 0: 
        pass
        #msgs.append(('info', u'Skipped empty new notes: {}'.format(emptynew)))
    return (good, old_notes, upd_notes, new_notes, del_notes)

def cnotes_c(vr, bk, ch, vs, myid, clause_atoms, changed, msgs):
    condition = u'''note.is_shared = 'T' or note.is_published = 'T' '''
    if myid != None: condition += u''' or note.created_by = {} '''.format(myid)

    note_sql = u'''
select
    note.id,
    note.created_by as uid,
    shebanq_web.auth_user.first_name as ufname,
    shebanq_web.auth_user.last_name as ulname,
    note.clause_atom,
    note.is_shared,
    note.is_published,
    note.published_on,
    note.status,
    note.keywords,
    note.ntext
from note inner join shebanq_web.auth_user
on note.created_by = shebanq_web.auth_user.id
where
    ({cond})
and
    note.version = '{vr}'
and
    note.book ='{bk}'
and
    note.chapter = {ch}
and
    note.verse = {vs}
order by
    modified_on desc
;
'''.format(
    cond=condition,
    vr=vr,
    bk=bk,
    ch=ch,
    vs=vs,
)

    records = note_db.executesql(note_sql)
    users = {}
    notes_proto = collections.defaultdict(lambda: {})
    ca_users = collections.defaultdict(lambda: collections.OrderedDict())
    if myid != None:
        users[myid] = u'me'
        for ca in clause_atoms:
            notes_proto[ca][myid] = [dict(uid=myid, nid=0, shared=True, pub=False, stat=u'o', kw='', ntxt=u'')]
            ca_users[ca][myid] = None
    good = True
    if records == None:
        msgs.append(('error', u'Cannot lookup notes for {} {}:{} in version {}'.format(bk, ch, vs, vr)))
        good = False
    elif len(records) == 0:
        pass
        #msgs.append(('info', u'No notes for {} {}:{} in version {}'.format(bk, ch, vs, vr)))
    else:
        for (nid, uid, ufname, ulname, ca, shared, pub, pub_on, status, keywords, ntext) in records:
            if (myid == None or (uid != myid)) and uid not in users:
                users[uid] = u'{} {}'.format(ufname, ulname)
            if uid not in ca_users[ca]: ca_users[ca][uid] = None
            pub = pub == 'T'
            shared = pub or shared == 'T'
            ro = myid == None or uid != myid or (pub and (pub_on <= request.now - PUBLISH_FREEZE))
            notes_proto.setdefault(ca, {}).setdefault(uid, []).append(dict(
                uid=uid,
                nid=nid,
                ro=ro,
                shared=shared,
                pub=pub,
                stat=status,
                kw=keywords,
                ntxt=ntext,
            ))
    notes = {}
    for ca in notes_proto:
        for uid in ca_users[ca]:
            notes.setdefault(ca, []).extend(notes_proto[ca][uid])

    return json.dumps(dict(good=good, changed=changed, msgs=msgs, users=users, notes=notes))

def sidem():
    session.forget(response)
    vr = get_request_val('material', '', 'version')
    qw = get_request_val('material', '', 'qw')
    bk = get_request_val('material', '', 'book')
    ch = get_request_val('material', '', 'chapter')
    pub = get_request_val('highlights', qw, 'pub') if qw != 'w' else ''
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
            monad_sets = get_q_hits(vr, chapter, pub)
            side_items = groupq(vr, monad_sets)
        elif qw == 'w':
            monad_sets = get_w_occs(vr, chapter)
            side_items = groupw(vr, monad_sets)
        elif qw == 'n':
            side_items = get_notes(vr, book, chapter, pub)
        else:
            side_items = []
        result = dict(
            colorpicker=colorpicker,
            side_items=side_items,
            qw=qw,
        )
    return result

def query():
    iidrep = get_request_val('material', '', 'iid')
    if request.extension == 'json':
        (authorized, msg) = item_access_read(iidrep=iidrep)
        if not authorized:
            result = dict(good=False, msg=[msg])
        else:
            vr = get_request_val('material', '', 'version')
            msgs = []
            (iid, kw) = iid_decode('q', iidrep)
            qrecord = get_query_info(iid, vr, msgs, with_ids=False, single_version=False, po=True)
            result = dict(good=qrecord != None, msg=msgs, data=qrecord)
            return dict(data=json.dumps(result))
    else:
        request.vars['mr'] = 'r'
        request.vars['qw'] = 'q'
        request.vars['tp'] = 'txt_p'
        request.vars['page'] = 1
    return text()

def word():
    request.vars['mr'] = 'r'
    request.vars['qw'] = 'w'
    request.vars['tp'] = 'txt_p'
    request.vars['page'] = 1
    return text()

def note():
    request.vars['mr'] = 'r'
    request.vars['qw'] = 'n'
    request.vars['tp'] = 'txt_p'
    request.vars['page'] = 1
    return text()

def csv(data): # converts an data structure of rows and fields into a csv string, with proper quotations and escapes
    result = []
    if data != None:
        for row in data:
            prow = [unicode(x) for x in row]
            trow = [u'"{}"'.format(x.replace(u'"',u'""')) if '"' in x or '\n' in x or '\r' in x or ',' in x else x for x in prow]
            result.append(u','.join(trow))
    return u'\n'.join(result)

def item(): # controller to produce a csv file of query results or lexeme occurrences, where fields are specified in the current legend
    vr = get_request_val('material', '', 'version')
    iidrep = get_request_val('material', '', 'iid')
    qw = get_request_val('material', '', 'qw')
    tp = get_request_val('material', '', 'tp')
    extra = get_request_val('rest', '', 'extra')
    if extra: extra = '_'+extra
    if len(extra) > 64: extra = extra[0:64]
    (iid, kw) = iid_decode(qw, iidrep)
    iidrep2 = iid_decode(qw, iidrep, rsep=u' ')
    filename = u'{}_{}{}_{}{}.csv'.format(vr, style[qw]['t'], iidrep2, tp_labels[tp], extra)
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        return dict(filename=filename, data=msg)
    hfields = get_fields(tp, qw=qw)
    if qw != 'n':
        head_row = ['book', 'chapter', 'verse'] + [hf[1] for hf in hfields]
        (nmonads, monad_sets) = load_q_hits(vr, iid) if qw == 'q' else load_w_occs(vr, iid)
        monads = flatten(monad_sets)
        data = []
        if len(monads):
            sql = u'''
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
;
'''.format(
                hflist=u', '.join(u'word.{}'.format(hf[0]) for hf in hfields),
                monads=u','.join(str(x) for x in monads),
            )
            data = passage_dbs[vr].executesql(sql)
    else:
        head_row = ['book', 'chapter', 'verse'] + [hf[1] for hf in hfields]
        kw_sql = kw.replace(u"'", u"''")
        myid = auth.user.id if auth.user != None else None
        extra = u''' or created_by = {} '''.format(uid) if myid == iid else u''
        sql = u'''
select
    shebanq_note.note.book, shebanq_note.note.chapter, shebanq_note.note.verse,
    {hflist}
from shebanq_note.note
inner join shebanq_note.key_note on shebanq_note.key_note.note_id = shebanq_note.note.id
inner join book on shebanq_note.note.book = book.name
inner join clause_atom on clause_atom.ca_num = shebanq_note.note.clause_atom and clause_atom.book_id = book.id
where key_note.keyword = '{kw}' and note.version = '{vr}' and (note.is_shared = 'T' {ex})
;
'''.format(
            hflist=u', '.join(hf[0] for hf in hfields),
            kw=kw_sql,
            vr=vr,
            ex=extra,
        )
        data = passage_dbs[vr].executesql(sql)
    return dict(filename=filename, data=csv([head_row]+list(data)))

def chart(): # controller to produce a chart of query results or lexeme occurrences
    vr = get_request_val('material', '', 'version')
    iidrep = get_request_val('material', '', 'iid')
    qw = get_request_val('material', '', 'qw')
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        result = get_chart(vr, [])
        result.update(qw=qw)
        return result()
    return from_cache(
        'chart_{}_{}_{}_'.format(vr, qw, iidrep),
        lambda: chart_c(vr, qw, iidrep),
        None,
    )

def chart_c(vr, qw, iidrep): 
    (iid, kw) = iid_decode(qw, iidrep)
    (nmonads, monad_sets) = load_q_hits(vr, iid) if qw == 'q' else load_w_occs(vr, iid) if qw == 'w' else load_n_notes(vr, iid, kw)
    result = get_chart(vr, monad_sets)
    result.update(qw=qw)
    return result

def sideqm():
    session.forget(response)
    iidrep = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if authorized:
        msg = u'fetching query'
    return dict(load=LOAD('hebrew', 'sideq', extension='load',
        vars=dict(mr='r', qw='q', version=vr, iid=iidrep),
        ajax=False, ajax_trap=True, target='querybody', 
        content=msg,
    ))

def sidewm():
    session.forget(response)
    iidrep = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if authorized:
        msg = u'fetching word'
    return dict(load=LOAD('hebrew', 'sidew', extension='load',
        vars=dict(mr='r', qw='w', version=vr, iid=iidrep),
        ajax=False, ajax_trap=True, target='wordbody', 
        content=msg,
    ))

def sidenm():
    session.forget(response)
    iidrep = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    msg = u'Not a valid id {}'.format(iidrep)
    if iidrep:
        msg = u'fetching note set'
    return dict(load=LOAD('hebrew', 'siden', extension='load',
        vars=dict(mr='r', qw='n', version=vr, iid=iidrep),
        ajax=False, ajax_trap=True, target='notebody', 
        content=msg,
    ))

def sideq():
    session.forget(response)
    msgs = []
    iidrep = get_request_val('material', '', 'iid')
    vr = get_request_val('material', '', 'version')
    (iid, kw) = iid_decode('q', iidrep)
    (authorized, msg) = query_auth_read(iid)
    if iid == 0 or not authorized:
        msgs.append(('error', msg))
        return dict(
            writable=False,
            iidrep = iidrep,
            vr = vr,
            qr = dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    q_record = get_query_info(iid, vr, msgs, with_ids=True, single_version=False, po=True)
    if q_record == None:
        return dict(
            writable=True,
            iidrep = iidrep,
            vr = vr,
            qr = dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )

    (authorized, msg) = query_auth_write(iid=iid)

    return dict(
        writable=authorized,
        iidrep = iidrep,
        vr = vr,
        qr = q_record,
        q=json.dumps(q_record),
        msgs=json.dumps(msgs),
    )

def sidew():
    session.forget(response)
    msgs = []
    vr = get_request_val('material', '', 'version')
    iidrep = get_request_val('material', '', 'iid')
    (iid, kw) = iid_decode('w', iidrep)
    (authorized, msg) = word_auth_read(vr, iid)
    if not authorized:
        msgs.append(('error', msg))
        return dict(
            wr=dict(),
            w=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    w_record = get_word_info(iid, vr, msgs)
    return dict(
        vr=vr,
        wr=w_record,
        w=json.dumps(w_record),
        msgs=json.dumps(msgs),
    )

def siden():
    session.forget(response)
    msgs = []
    vr = get_request_val('material', '', 'version')
    iidrep = get_request_val('material', '', 'iid')
    (iid, kw) = iid_decode('n', iidrep)
    if not iid:
        msg = u'Not a valid id {}'.format(iid)
        msgs.append(('error', msg))
        return dict(
            nr=dict(),
            n=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    n_record = get_note_info(iidrep, vr, msgs)
    return dict(
        vr=vr,
        nr=n_record,
        n=json.dumps(n_record),
        msgs=json.dumps(msgs),
    )

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
    qid = check_id('goto', 'q', 'query', msgs)
    if qid != None:
        if not query_auth_read(qid): qid = 0
    return dict(qid=qid)

def notes():
    msgs = []
    nkid = check_id('goto', 'n', 'note', msgs)
    return dict(nkid=nkid)

def words_page(viewsettings, vr, lan=None, letter=None):
    (letters, words) = from_cache('words_data_{}_'.format(vr), lambda: get_words_data(vr), None)
    return dict(versionstate=viewsettings.versionstate(), lan=lan, letter=letter, letters=letters, words=words.get(lan, {}).get(letter, []))

def get_words_data(vr):
    ddata = passage_dbs[vr].executesql(u'''
select id, entry_heb, entryid_heb, lan, gloss from lexicon order by lan, entryid_heb
;
''')
    letters = dict(arc=[], hbo=[])
    words = dict(arc={}, hbo={})
    for (wid, e, eid, lan, gloss) in ddata:
        letter = ord(e[0])
        if letter not in words[lan]:
            letters[lan].append(letter)
            words[lan][letter] = []
        words[lan][letter].append((e, wid, eid, gloss))
    return (letters, words)

def get_word_info(iid, vr, msgs):
    sql = u'''
select * from lexicon where id = '{}'
;
'''.format(iid)
    w_record = dict(id=iid, versions={})
    for v in versions:
        if not versions[v]['date']: continue
        records = passage_dbs[v].executesql(sql, as_dict=True)
        if records == None:
            msgs.append(('error', u'Cannot lookup word with id {} in version'.format(iid, v)))
        elif len(records) == 0:
            msgs.append(('warning', u'No word with id {} in version {}'.format(iid, v)))
        else:
            w_record['versions'][v] = records[0]
    return w_record

def get_note_info(iidrep, vr, msgs):
    (iid, kw) = iid_decode('n', iidrep)
    if iid == None: return {}
    n_record = dict(id=iidrep, uid=iid, ufname='N?', ulname='N?', kw=kw, versions={})
    n_record['versions'] = count_n_notes(iid, kw)
    sql = u'''
select first_name, last_name from auth_user where id = '{}'
;
'''.format(iid)
    uinfo = db.executesql(sql)
    if uinfo != None and len(uinfo) > 0:
        n_record['ufname'] = uinfo[0][0]
        n_record['ulname'] = uinfo[0][1]
    return n_record

def get_query_info(iid, vr, msgs, single_version=False, with_ids=True, po=False):
    sqli = u''',
    query.created_by as uid,
    project.id as pid,
    organization.id as oid
''' if with_ids and po else u''

    sqlx = u''',
    query_exe.id as xid,
    query_exe.mql as mql,
    query_exe.version as version,
    query_exe.eversion as eversion,
    query_exe.resultmonads as resultmonads,
    query_exe.results as results,
    query_exe.executed_on as executed_on,
    query_exe.modified_on as xmodified_on,
    query_exe.is_published as is_published,
    query_exe.published_on as published_on
''' if single_version else u''

    sqlp = u''',
    project.name as pname,
    project.website as pwebsite,
    organization.name as oname,
    organization.website as owebsite
''' if po else u''

    sqlm = u'''
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

    sqlr = u'''
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{}'
'''.format(vr) if single_version else u''

    sqlpr = u'''
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
''' if po else u''

    sqlc = u'''
where query.id in ({})
'''.format(u','.join(iid)) if single_version else u'''
where query.id = {}
'''.format(iid)

    sqlo = u'''
order by auth_user.last_name, query.name
''' if single_version else u''

    sql = u'''
select{} from query inner join auth_user on query.created_by = auth_user.id {}{}{}{}
;
'''.format(sqlm, sqlr, sqlpr, sqlc, sqlo)
    records = db.executesql(sql, as_dict=True)
    if records == None:
        msgs.append(('error', u'Cannot lookup query(ies)'))
        return None
    if single_version:
        for q_record in records:
            query_fields(vr, q_record, [], single_version=True)
        return records
    else:
        if len(records) == 0:
            msgs.append(('error', u'No query with id {}'.format(iid)))
            return None
        q_record = records[0]
        q_record['description_md'] = markdown(q_record['description'])
        sql = u'''
select
    id as xid,
    mql,
    version,
    eversion,
    resultmonads,
    results,
    executed_on,
    modified_on as xmodified_on,
    is_published,
    published_on
from query_exe
where query_id = {}
;
'''.format(iid)
        recordx = db.executesql(sql, as_dict=True)
        query_fields(vr, q_record, recordx, single_version=False)
        return q_record

def pagelist(page, pages, spread):
    factor = 1
    filtered_pages = {1, page, pages}
    while factor <= pages:
        page_base = factor * int(page / factor)
        filtered_pages |= {page_base + int((i - spread / 2) * factor) for i in range(2 * int(spread / 2) + 1)} 
        factor *= spread
    return sorted(i for i in filtered_pages if i > 0 and i <= pages) 

def query_tree():
    myid = None
    if auth.user:
        myid = auth.user.id
    linfo = collections.defaultdict(lambda: {})

    def title_badge(lid, ltype, newtype, publ, good, num, tot):
        name = linfo[ltype][lid] if ltype != None else u'Shared Queries'
        nums = []
        if publ != 0: nums.append(u'<span class="special fa fa-quote-right"> {}</span>'.format(publ))
        if good != 0: nums.append(u'<span class="good fa fa-gears"> {}</span>'.format(good))
        badge = ''
        if len(nums) == 0:
            if tot == num:
                badge = u'<span class="total">{}</span>'.format(u', '.join(nums))
            else:
                badge = u'{} of <span class="total">{}</span>'.format(u', '.join(nums), tot)
        else:
            if tot == num:
                badge = u'{} of <span class="total">{}</span>'.format(u', '.join(nums), num)
            else:
                badge = u'{} of {} of all <span class="total">{}</span>'.format(u', '.join(nums), num, tot)
        rename = u''
        create = u''
        select = u''
        if myid != None:
            if newtype != None:
                create = u'<a class="n_{}" href="#"></a>'.format(newtype)
            if ltype in {'o', 'p'}:
                if lid:
                    rename = u'<a class="r_{}" lid="{}" href="#"></a>'.format(ltype, lid)
                select = u'<a class="s_{} fa fa-lg" lid="{}" href="#"></a>'.format(ltype, lid)
        return u'{} <span n="1">{}</span><span class="brq">({})</span> {} {}'.format(select, h_esc(name), badge, rename, create)

    condition = u'''
where query.is_shared = 'T'
''' if myid == None else '''
where query.is_shared = 'T' or query.created_by = {}
'''.format(myid)

    pqueryx_sql = u'''
select
    query_exe.query_id, query_exe.version, query_exe.is_published, query_exe.published_on, query_exe.modified_on, query_exe.executed_on
from query_exe
inner join query on query.id = query_exe.query_id
{};
'''.format(condition)

    pquery_sql = u'''
select
    query.id as qid,
    organization.name as oname, organization.id as oid,
    project.name as pname, project.id as pid,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname, auth_user.id as uid,
    query.name as qname, query.is_shared as is_shared
from query
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
inner join auth_user on query.created_by = auth_user.id
{}
order by organization.name, project.name, auth_user.last_name, auth_user.first_name, query.name
;
'''.format(condition)

    pquery = db.executesql(pquery_sql)
    pqueryx = db.executesql(pqueryx_sql)
    pqueries = collections.OrderedDict()
    rversion_order = [v for v in version_order if versions[v]['date']]
    rversion_index = dict((x[1],x[0]) for x in enumerate(rversion_order)) 
    for (qid, oname, oid, pname, pid, uname, uid, qname, qshared) in pquery:
        qsharedstatus = qshared == 'T'
        qownstatus = uid == myid
        pqueries[qid] = {'': (oname, oid, pname, pid, uname, uid, qname, qsharedstatus, qownstatus), 'publ': False, 'good': False, 'v': [4 for v in rversion_order]}
    for (qid, vr, qispub, qpub, qmod, qexe) in pqueryx:
        qinfo = pqueries[qid]
        qexestatus = None
        if qexe: qexestatus = qexe >= qmod
        qpubstatus = False if qispub != 'T' else None if qpub > request.now - PUBLISH_FREEZE else True
        qstatus = 1 if qpubstatus else 2 if qpubstatus == None else 3 if qexestatus else 4 if qexestatus == None else 5
        qinfo['v'][rversion_index[vr]] = qstatus
        if qpubstatus or qpubstatus == None: qinfo['publ'] = True
        if qexestatus: qinfo['good'] = True


    porg_sql = u'''
select name, id from organization order by name
;
'''
    porg = db.executesql(porg_sql)

    pproj_sql = u'''
select name, id from project order by name
;
'''
    pproj = db.executesql(pproj_sql)

    tree = collections.OrderedDict()
    countset = collections.defaultdict(lambda: set())
    counto = collections.defaultdict(lambda: 0)
    counto_publ = collections.defaultdict(lambda: 0)
    counto_good = collections.defaultdict(lambda: 0)
    counto_tot = collections.defaultdict(lambda: 0)
    countp = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_publ = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_good = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    countp_tot = collections.defaultdict(lambda: 0)
    countu = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_publ = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_good = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))
    countu_tot = collections.defaultdict(lambda: 0)
    count = 0
    count_publ = 0
    count_good = 0
    for qid in pqueries:
        pqinfo = pqueries[qid]
        (oname, oid, pname, pid, uname, uid, qname, qshared, qown) = pqinfo['']
        qpubl = pqinfo['publ']
        qgood = pqinfo['good']
        countset['o'].add(oid)
        countset['p'].add(pid)
        countset['u'].add(uid)
        countset['q'].add(qid)
        linfo['o'][oid] = oname
        linfo['p'][pid] = pname
        linfo['u'][uid] = uname
        if qown:
            countset['m'].add(qid)
        if not qshared:
            countset['r'].add(qid)
        if qpubl:
            countu_publ[oid][pid][uid] += 1
            countp_publ[oid][pid] += 1
            counto_publ[oid] += 1
            count_publ += 1
        if qgood:
            countu_good[oid][pid][uid] += 1
            countp_good[oid][pid] += 1
            counto_good[oid] += 1
            count_good += 1
        tree.setdefault(oid, collections.OrderedDict()).setdefault(pid, collections.OrderedDict()).setdefault(uid, []).append(qid)
        count +=1
        counto[oid] += 1
        countp[oid][pid] += 1
        countu[oid][pid][uid] += 1
        counto_tot[oid] += 1
        countp_tot[pid] += 1
        countu_tot[uid] += 1

    linfo['o'][0] = u'Projects without Queries'
    linfo['p'][0] = u'New Project'
    linfo['u'][0] = u''
    linfo['q'] = pqueries
    counto[0] = 0
    countp[0][0] = 0
    for (oname, oid) in porg:
        if oid in linfo['o']: continue
        countset['o'].add(oid)
        linfo['o'][oid] = oname
        tree[oid] = collections.OrderedDict()

    for (pname, pid) in pproj:
        if pid in linfo['p']: continue
        countset['o'].add(0)
        countset['p'].add(pid)
        linfo['p'][pid] = pname
        tree.setdefault(0, collections.OrderedDict())[pid] = collections.OrderedDict()

    ccount = dict((x[0], len(x[1])) for x in countset.items())
    ccount['uid'] = myid
    title = title_badge(None, None, 'o', count_publ, count_good, count, count)
    dest = [dict(title=u'{}'.format(title), folder=True, children=[], data=ccount)]
    curdest = dest[-1]['children']
    cursource = tree
    for oid in cursource:
        onum = counto[oid]
        opubl = counto_publ[oid]
        ogood = counto_good[oid]
        otot = counto_tot[oid]
        otitle = title_badge(oid, 'o', 'p', opubl, ogood, onum, otot)
        curdest.append(dict(title=u'{}'.format(otitle), folder=True, children=[]))
        curodest = curdest[-1]['children']
        curosource = cursource[oid]
        for pid in curosource:
            pnum = countp[oid][pid]
            ppubl = countp_publ[oid][pid]
            pgood = countp_good[oid][pid]
            ptot = countp_tot[pid]
            ptitle = title_badge(pid, 'p', 'q', ppubl, pgood, pnum, ptot)
            curodest.append(dict(title=u'{}'.format(ptitle), folder=True, children=[]))
            curpdest = curodest[-1]['children']
            curpsource = curosource[pid]
            for uid in curpsource:
                unum = countu[oid][pid][uid]
                upubl = countu_publ[oid][pid][uid]
                ugood = countu_good[oid][pid][uid]
                utot = countu_tot[uid]
                utitle = title_badge(uid, 'u', None, upubl, ugood, unum, utot)
                curpdest.append(dict(title=u'{}'.format(utitle), folder=True, children=[]))
                curudest = curpdest[-1]['children']
                curusource = curpsource[uid]
                for qid in curusource:
                    pqinfo = linfo['q'][qid]
                    (oname, oid, pname, pid, uname, uid, qname, qshared, qown) = pqinfo['']
                    qpubl = pqinfo['publ']
                    qgood = pqinfo['good']
                    qversions = pqinfo['v']
                    rename = u'<a class="{}_{}" lid="{}" href="#"></a>'.format('r' if qown else 'v', 'q', qid)
                    curudest.append(dict(title=u'{} <a class="q {} {}" n="1" qid="{}" href="#">{}</a> <a class="md" href="#"></a> {}'.format(
                        u' '.join(formatversion('q', qid, v, qversions[rversion_index[v]]) for v in rversion_order),
                        u'qmy' if qown else u'',
                        u'' if qshared else u'qpriv',
                        iid_encode('q', qid),
                        h_esc(qname),
                        rename,
                    ), key=u'q{}'.format(qid), folder=False))
    return dict(data=json.dumps(dest))

def note_tree():
    myid = None
    if auth.user:
        myid = auth.user.id
    linfo = collections.defaultdict(lambda: {})

    def title_badge(lid, ltype, tot):
        name = linfo[ltype][lid] if ltype != None else u'Shared Notes'
        badge = ''
        if tot != 0:
            badge = u'<span class="total special"> {}</span>'.format(tot)
        return u'<span n="1">{}</span><span class="brn">({})</span>'.format(h_esc(name), badge)

    condition = u'''
where note.is_shared = 'T'
''' if myid == None else '''
where note.is_shared = 'T' or note.created_by = {}
'''.format(myid)

    pnotek_sql = u'''
select keyword, note_id from key_note
order by keyword
;
'''
    pnotek = note_db.executesql(pnotek_sql)
    pnote_sql = u'''
select
    note.id,
    note.version,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname, auth_user.id as uid
from note
inner join shebanq_web.auth_user on note.created_by = shebanq_web.auth_user.id
{}
order by shebanq_web.auth_user.last_name, shebanq_web.auth_user.first_name, note.keywords
;
'''.format(condition)

    pnote = note_db.executesql(pnote_sql)
    kindex = collections.defaultdict(lambda: [])
    for (k, nid) in pnotek:
        kindex[nid].append(k)
    pnotes = collections.OrderedDict()
    rversion_order = [v for v in version_order if versions[v]['date']]
    rversion_index = dict((x[1],x[0]) for x in enumerate(rversion_order)) 
    for (nid, nvr, uname, uid) in pnote:
        for kw in kindex[nid]:
            nkid = iid_encode('n', uid, kw=kw)
            if nkid not in pnotes:
                pnotes[nkid] = {'': (uname, uid, kw), 'v': [0 for v in rversion_order]}
            pnotes[nkid]['v'][rversion_index[nvr]] += 1

    tree = collections.OrderedDict()
    countset = collections.defaultdict(lambda: set())
    countu = collections.defaultdict(lambda: 0)
    count = 0
    for nkid in pnotes:
        pninfo = pnotes[nkid]
        (uname, uid, nname) = pninfo['']
        countset['u'].add(uid)
        countset['n'].add(nkid)
        linfo['u'][uid] = uname
        tree.setdefault(uid, []).append(nkid)
        count +=1
        countu[uid] += 1

    linfo['u'][0] = u''
    linfo['n'] = pnotes

    ccount = dict((x[0], len(x[1])) for x in countset.items())
    ccount['uid'] = myid
    title = title_badge(None, None, count)
    dest = [dict(title=u'{}'.format(title), folder=True, children=[], data=ccount)]
    curdest = dest[-1]['children']
    cursource = tree
    for uid in cursource:
        utot = countu[uid]
        utitle = title_badge(uid, 'u', utot)
        curdest.append(dict(title=u'{}'.format(utitle), folder=True, children=[]))
        curudest = curdest[-1]['children']
        curusource = cursource[uid]
        for nkid in curusource:
            pninfo = linfo['n'][nkid]
            (uname, uid, nname) = pninfo['']
            nversions = pninfo['v']
            curudest.append(dict(
                title=u'{} <a class="n t1_kw" n="1" nkid="{}" href="#">{}</a> <a class="md" href="#"></a>'.format(
                        u' '.join(formatversion('n', nkid, v, nversions[rversion_index[v]]) for v in rversion_order),
                        nkid,
                        h_esc(nname),
                    ),
                key=u'n{}'.format(nkid), folder=False),
            )
    return dict(data=json.dumps(dest))

def formatversion(qw, lid, vr, st):
    if qw == 'q':
        if st == 1:
            icon = 'quote-right'
            cls = 'special'
        elif st == 2:
            icon = 'quote-right'
            cls = ''
        elif st == 3:
            icon = 'gears'
            cls = 'good'
        elif st == 4:
            icon = 'circle-o'
            cls = 'warning'
        elif st == 5:
            icon = 'clock-o'
            cls = 'error'
        return u'<a href="#" class="ctrl br{} {} fa fa-{}" {}id="{}" v="{}"></a>'.format(qw, cls, icon, qw, lid, vr)
    else:
        return u'<a href="#" class="ctrl br{}" nkid="{}" v="{}">{}</a>'.format(qw, lid, vr, st if st else '-')

tps = dict(o=('organization', 'organization'), p=('project', 'project'), q=('query', 'query'))

def check_unique(tp, lid, val, myid, msgs):
    result = False
    (label, table) = tps[tp]
    for x in [1]:
        if tp == 'q':
            check_sql = u'''
select id from query where name = '{}' and query.created_by = {}
;
'''.format(val, myid)
        else:
            check_sql = u'''
select id from {} where name = '{}'
;
'''.format(table, val)
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
        if val == u'':
            msgs.append(('error', u'{label} name consists completely of white space!'.format(label=label)))
            break
        val = val.replace(u"'",u"''")
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
        result = val.replace(u"'",u"''")
    return result

def check_mql(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 8192:
            msgs.append(('error', u'{label} mql is longer than 8192 characters!'.format(label=label)))
            break
        result = val.replace(u"'",u"''")
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
        result = urlunparse(url_comps).replace(u"'",u"''")
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

def check_id(var, tp, label, msgs):
    valrep = request.vars[var]
    if valrep == None:
        msgs.append(('error', u'No {} id given'.format(label)))
        return None
    if tp in {'w', 'q', 'n'}:
        (val, kw) = iid_decode(tp, valrep)
    else:
        val = valrep
        if len(valrep) > 10 or not valrep.isdigit():
            msgs.append(('error', u'Not a valid {} id'.format(label)))
            return None
        val = int(valrep)
    if tp == 'n': return valrep
    return val

def check_rel(tp, val, msgs):
    (label, table) = tps[tp]
    result = None
    for x in [1]:
        check_sql = u'''
select count(*) as occurs from {} where id = '{}'
;
'''.format(table, val)
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
        if tp not in tps:
            msgs.append(('error', u'unknown type {}!'.format(tp)))
            break
        (label, table) = tps[tp]
        lid = check_id('lid', tp, label, msgs)
        upd = request.vars.upd
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
                oid = check_id('oid', 'o', tps['o'][0], msgs)
                pid = check_id('pid', 'p', tps['o'][0], msgs)
                if oid == None or pid == None: break
                osql = u'''
select id as oid, name as oname, website as owebsite from organization where id = {}
;
'''.format(oid)
                psql = u'''
select id as pid, name as pname, website as pwebsite from project where id = {}
;
'''.format(pid)
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
;
'''.format(lid), as_dict=True)
        else:
            if lid == 0:
                pass
            else:
                dbrecord = db.executesql(u'''
select {} from {} where id = {}
;
'''.format(u','.join(fields), table, lid), as_dict=True)
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
            val = check_id('oid', 'o', tps['o'][0], msgs)
            if val == None: break
            valsql = check_rel('o', val, msgs)
            if valsql == None: break
            updrecord['organization'] = valsql
            val = check_id('pid', 'p', tps['p'][0], msgs)
            valsql = check_rel('p', val, msgs)
            if valsql == None: break
            updrecord['project'] = valsql
            fld = 'modified_on' 
            updrecord[fld] = request.now
            fields.append(fld)
            if lid == 0:
                fld = 'created_on' 
                updrecord[fld] = request.now
                fields.append(fld)
                fld = 'created_by' 
                updrecord[fld] = myid
                fields.append(fld)
        else:
            valsql = check_website(tp, request.vars.website, msgs)
            if valsql == None:
                break
            updrecord['website'] = valsql
        good = True
    if good:
        if lid:
            fieldvals = [u" {} = '{}'".format(f, updrecord[f]) for f in fields]
            sql = u'''update {} set{} where id = {};'''.format(table, u','.join(fieldvals), lid)
            thismsg = 'updated'
        else:
            fieldvals = [u"'{}'".format(updrecord[f]) for f in fields]
            sql = u'''
insert into {} ({}) values ({})
;
'''.format(table, u','.join(fields), u','.join(fieldvals), lid)
            thismsg = u'added'
        result = db.executesql(sql)
        if lid == 0:
            lid = db.executesql(u'''
select last_insert_id() as x
;
''')[0][0]

        msgs.append((u'good', thismsg))
    return (good, lid)

def field():
    msgs = []
    good = False
    mod_date_fld = None
    mod_dates = {}
    extra = {}
    myid = auth.user.id if auth.user != None else None
    for x in [1]:
        qid = check_id('qid', 'q', 'query', msgs)
        if qid == None: break
        fname = request.vars.fname
        val = request.vars.val
        vr = request.vars.version
        if fname == None or fname not in {'is_shared', 'is_published'}:
            msgs.append('error', u'Illegal field name {}')
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
    clear_cache(r'^items_q_')
    fieldval = u" {} = '{}'".format(fname, valsql)
    mod_date = request.now.replace(microsecond=0) if valsql == 'T' else None
    mod_date_sql = 'null' if mod_date == None else u"'{}'".format(mod_date)
    fieldval += u', {} = {} '.format(mod_date_fld, mod_date_sql) 
    sql = u'''
update {} set{} where id = {}
;
'''.format(table, fieldval, qid)
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
    clear_cache(r'^items_q_{}_'.format(vr))
    verify_version(qid, vr)
    fieldval = u" {} = '{}'".format(fname, valsql)
    mod_date = request.now.replace(microsecond=0) if valsql == 'T' else None
    mod_date_sql = 'null' if mod_date == None else u"'{}'".format(mod_date)
    fieldval += u', {} = {} '.format(mod_date_fld, mod_date_sql) 
    sql = u'''
update {} set{} where query_id = {} and version = '{}'
;
'''.format(table, fieldval, qid, vr)
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
            sql = u'''
select count(*) from query_exe where query_id = {} and is_published = 'T'
;
'''.format(qid)
            pv = db.executesql(sql)
            has_public_versions = pv != None and len(pv) == 1 and pv[0][0] > 0
            if has_public_versions:
                msgs.append(('error', u'You cannot UNshare this query because there is a published execution record'))
                break
        if fname == 'is_published':
            mod_cls['#is_pub_ro'] = u'fa-{}'.format('check' if valsql == 'T' else 'close')
            mod_cls['div[version="{}"]'.format(vr)] = 'published' if valsql == 'T' else 'unpublished'
            extra['execq'] = ('show', valsql != 'T')
            if valsql == 'T':
                sql = u'''
select executed_on, modified_on as xmodified_on from query_exe where query_id = {} and version = '{}'
;
'''.format(qid, vr)
                pv = db.executesql(sql, as_dict=True)
                if pv == None or len(pv) != 1:
                    msgs.append(('error', u'cannot determine whether query results are up to date'))
                    break
                uptodate = qstatus(pv[0])
                if uptodate != 'good':
                    msgs.append(('error', u'You can only publish if the query results are up to date'))
                    break
                sql = u'''
select is_shared from query where id = {}
;
'''.format(qid)
                pv = db.executesql(sql)
                is_shared = pv != None and len(pv) == 1 and pv[0][0] == 'T'
                if not is_shared:
                    (mod_date_fld, mod_date) = upd_shared(myid, qid, 'T', msgs)
                    mod_dates[mod_date_fld] = mod_date
                    extra['is_shared'] = ('checked', True)
            else:
                sql = u'''
select published_on from query_exe where query_id = {} and version = '{}'
;
'''.format(qid, vr)
                pv = db.executesql(sql)
                pdate_ok = pv == None or len(pv) != 1 or pv[0][0] == None or pv[0][0] > request.now - PUBLISH_FREEZE
                if not pdate_ok:
                    msgs.append(('error', u'You cannot UNpublish this query because it has been published more than {} ago'.format(PUBLISH_FREEZE_MSG)))
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
    exist_version = db.executesql(u'''
select id from query_exe where version = '{}' and query_id = {}
;
'''.format(vr, qid))
    if exist_version == None or len(exist_version) == 0:
        db.executesql(u'''
insert into query_exe (id, version, query_id) values (null, '{}', {})
;
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
        qid = check_id('qid', 'q', 'query', msgs)
        if qid == None: break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(('error', msg))
            break
        
        verify_version(qid, vr)
        oldrecord = db.executesql(u'''
select
    query.name as name,
    query.description as description,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{}'
where query.id = {}
;
'''.format(vr, qid), as_dict=True)
        if oldrecord == None or len(oldrecord) == 0:
            msgs.append(('error', u'No query with id {}'.format(qid)))
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
            newmql_u = unicode(newmql, encoding='utf-8')
            if oldvals['mql'] != newmql_u:
                msgs.append(('warning', u'query body modified'))
                valsql = check_mql('q', newmql_u, msgs)
                if valsql == None:
                    break
                fldx['mql'] = valsql
                fldx['modified_on'] = request.now
            else:
                msgs.append(('good', u'same query body'))
        else:
            msgs.append(('warning', u'only the description can been saved because this is a published query execution'))
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
            (xgood, nresults, xmonads, this_msgs, eversion) = mql(vr, newmql) 
            if xgood:
                store_monad_sets(vr, qid, xmonads)
                fldx['executed_on'] = request.now
                fldx['eversion'] = eversion
                nresultmonads = count_monads(xmonads)
                fldx['results'] = nresults
                fldx['resultmonads'] = nresultmonads
                msgs.append(('good', u'Query executed'))
            else:
                store_monad_sets(vr, qid, [])
            msgs.extend(this_msgs)
        if len(flds):
            sql = u'''
update {} set{} where id = {}
;
'''.format(
                'query',
                u', '.join(u" {} = '{}'".format(f, flds[f]) for f in flds if f != 'status'),
                qid,
            )
            db.executesql(sql)
            clear_cache(r'^items_q_')
        if len(fldx):
            sql = u'''
update {} set{} where query_id = {} and version = '{}'
;
'''.format(
                'query_exe',
                u', '.join(u" {} = '{}'".format(f, fldx[f]) for f in fldx if f != 'status'),
                qid,
                vr,
            )
            db.executesql(sql)
            clear_cache(r'^items_q_{}_'.format(vr))
        q_record = get_query_info(qid, vr, msgs, with_ids=False, single_version=False, po=True)

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
            eversion=None,
            published_on=None,
        )) for v in versions if versions[v]['date'])
        for rx in recordx:
            vx = rx['version']
            dest = q_record['versions'][vx]
            dest.update(rx)
            dest['status'] = qstatus(dest)
            datetime_str(dest)

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
    bookrecords = passage_dbs[vr].executesql(u'''
select * from book where name = '{}'
;
'''.format(bookname), as_dict=True)
    book = bookrecords[0] if bookrecords else {}
    chapterrecords = passage_dbs[vr].executesql(u'''
select * from chapter where chapter_num = {} and book_id = {}
;
'''.format(chapternum, book['id']), as_dict=True)
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
        wsql = u'''
select * from lexicon where id in ({}) order by entryid_heb
;
'''.format(u','.join("'{}'".format(str(x)) for x in wids))
        wordrecords = passage_dbs[vr].executesql(wsql, as_dict=True)
        for w in wordrecords:
            r.append({'item': w, 'monads': json.dumps(wids[w['id']])})
    return r

def get_notes(vr, book, chapter, pub):
    bk = book['name']
    ch = chapter['chapter_num']
    if pub == 'x':
        pubv = ''
    else:
        pubv = " and is_published = 'T'"
    sql = u'''
select
    note.created_by,
    shebanq_web.auth_user.first_name,
    shebanq_web.auth_user.last_name,
    note.keywords,
    note.verse,
    note.is_published
from note
inner join shebanq_web.auth_user on shebanq_web.auth_user.id = created_by
where version = '{}' and book = '{}' and chapter = {} {}
order by note.verse
;
'''.format(vr, bk, ch, pubv)
    records = note_db.executesql(sql)
    user = {}
    npub = collections.Counter()
    nnotes = collections.Counter()
    nverses = {}
    for (uid, ufname, ulname, kw, v, pub) in records:
        if uid not in user: user[uid] = (ufname, ulname)
        for k in WORD_PAT.findall(kw):
            if pub == 'T': npub[(uid, k)] += 1
            nnotes[(uid, k)] += 1
            nverses.setdefault((uid, k), set()).add(v)
    r = []
    for (uid, k) in nnotes:
        (ufname, ulname) = user[uid]
        this_npub = npub[(uid, k)]
        this_nnotes = nnotes[(uid, k)]
        this_nverses = len(nverses[(uid, k)])
        r.append({
            'item': dict(
                    id=iid_encode('n', uid, k),
                    ufname=ufname,
                    ulname=ulname,
                    kw=k,
                    is_published=this_npub>0,
                    nnotes=this_nnotes,
                    nverses=this_nverses,
                ),
            'monads': json.dumps([]),
        })
    return r

def get_q_hits(vr, chapter, pub):
    if pub == 'x':
        pubv = u''
        pubx = u"inner join query on query.id = query_exe.query_id and query.is_shared = 'T'"
    else:
        pubv = u" and query_exe.is_published = 'T'"
        pubx = u''
    return db.executesql(u'''
select DISTINCT
    query_exe.query_id as query_id,
    GREATEST(first_m, {chapter_first_m}) as first_m,
    LEAST(last_m, {chapter_last_m}) as last_m
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and query_exe.executed_on >= query_exe.modified_on {pubv}
{pubx}
where
    (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    ({chapter_first_m} BETWEEN first_m AND last_m)
;
'''.format(
         chapter_last_m=chapter['last_m'],
         chapter_first_m=chapter['first_m'],
         vr=vr,
         pubv=pubv,
         pubx=pubx,
    ))

def get_w_occs(vr, chapter):
    return passage_dbs[vr].executesql(u'''
select anchor, lexicon_id
from word_verse
where anchor BETWEEN {chapter_first_m} AND {chapter_last_m}
;
'''.format(
         chapter_last_m=chapter['last_m'],
         chapter_first_m=chapter['first_m'],
    ))

def item_access_read(iidrep=get_request_val('material', '', 'iid')):
    mr = get_request_val('material', '', 'mr')
    qw = get_request_val('material', '', 'qw')
    if mr == 'm': return (True, '')
    if qw == 'w': return (True, '')
    if qw == 'n': return (True, '')
    if qw == 'q':
        if iidrep != None:
            (iid, kw) = iid_decode(qw, iidrep)
            if iid > 0: return query_auth_read(iid)
    return (None, u'Not a valid id {}'.format(iidrep))

def query_auth_read(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user != None
    else:
        q_records = db.executesql(u'''
select * from query where id = {}
;
'''.format(iid), as_dict=True)
        q_record = q_records[0] if q_records else {}
        if q_record:
            authorized = q_record['is_shared'] or (auth.user != None and q_record['created_by'] == auth.user.id)
    msg = u'No query with id {}'.format(iid) if authorized == None else u'You have no access to item with id {}'.format(iid) 
    return (authorized, msg)

def word_auth_read(vr, iid):
    authorized = None
    if not iid:
        authorized = False
    else:
        words = passage_dbs[vr].executesql(u'''
select * from lexicon where id = '{}'
;
'''.format(iid), as_dict=True)
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
        q_records = db.executesql(u'''
select * from query where id = {}
;
'''.format(iid), as_dict=True)
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
    recordx = db.executesql(u'''
select id from query_exe where query_id = {} and version = '{}'
;
'''.format(iid, vr))
    if recordx == None or len(recordx) != 1: return None
    return recordx[0][0]

def count_monads(rows):
    covered = set()
    for (b,e) in rows: covered |= set(xrange(b, e+1))
    return len(covered)

def store_monad_sets(vr, iid, rows):
    xid = get_qx(vr, iid)
    if xid == None: return
    db.executesql(u'''
delete from monads where query_exe_id={}
;
'''.format(xid))
    # Here we clear stuff that will become invalid because of a (re)execution of a query
    # and the deleting of previous results and the storing of new results.
    clear_cache(r'^verses_{}_q_{}_'.format(vr, iid))
    clear_cache(r'^items_q_{}_'.format(vr))
    clear_cache(r'^chart_{}_q_{}_'.format(vr, iid))
    nrows = len(rows)
    if nrows == 0: return

    limit_row = 10000
    start = u'''
insert into monads (query_exe_id, first_m, last_m) values
'''
    query = u''
    r = 0
    while r < nrows:
        if query != u'':
            db.executesql(query)
            query = u''
        query += start
        s = min(r + limit_row, len(rows))
        row = rows[r]
        query += u'({},{},{})'.format(xid, row[0], row[1])
        if r + 1 < nrows:
            for row in rows[r + 1:s]: 
                query += u',({},{},{})'.format(xid, row[0], row[1])
        r = s
    if query != u'':
        db.executesql(query)
        query = u''

def load_q_hits(vr, iid):
    xid = get_qx(vr, iid)
    if xid == None: return normalize_ranges([])
    monad_sets = db.executesql(u'''
select first_m, last_m from monads where query_exe_id = {} order by first_m
;
'''.format(xid))
    return normalize_ranges(monad_sets)

def load_w_occs(vr, lexeme_id):
    monads = passage_dbs[vr].executesql(u'''
select anchor from word_verse where lexicon_id = '{}' order by anchor
;
'''.format(lexeme_id))
    return collapse_into_ranges(monads)

def count_n_notes(uid, kw):
    kw_sql = kw.replace(u"'", u"''")
    myid = auth.user.id if auth.user != None else None
    extra = u''' or created_by = {} '''.format(uid) if myid == uid else u''
    sql = u'''
select version, book, chapter, verse, clause_atom, id from note
inner join key_note on key_note.note_id = note.id
where key_note.keyword = '{}' and (note.is_shared = 'T' {})
;'''.format(kw_sql, extra)
    records = note_db.executesql(sql)
    n_count = collections.Counter()
    c_count = collections.defaultdict(lambda: set())
    v_count = collections.defaultdict(lambda: set())
    vrs = set()
    for (vr, bk, ch, vs, ca, nid) in records:
        vrs.add(vr)
        n_count[vr] += 1
        c_count[vr].add((bk,ca))
        v_count[vr].add((bk,ch, vs))
    versions_info = {}
    for vr in versions:
        if not versions[vr]['date']: continue
        n = n_count.get(vr, 0)
        c = len(c_count.get(vr, set()))
        v = len(v_count.get(vr, set()))
        versions_info[vr] = dict(n=n, c=c, v=v)
    return versions_info

def load_n_notes(vr, iid, kw):
    clause_atom_first = from_cache('clause_atom_f_{}_'.format(vr), lambda: get_clause_atom_fmonad(vr), None)
    kw_sql = kw.replace(u"'", u"''")
    myid = auth.user.id if auth.user != None else None
    extra = u''' or created_by = {} '''.format(uid) if myid == iid else u''
    sql = u'''
select book, clause_atom from note
inner join key_note on key_note.note_id = note.id
where key_note.keyword = '{}' and note.version = '{}' and (note.is_shared = 'T' {})
;
'''.format(kw_sql, vr, extra)
    clause_atoms = note_db.executesql(sql)
    monads = {clause_atom_first[x[0]][x[1]] for x in clause_atoms} 
    return normalize_ranges(None, fromset=monads)

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

def get_pagination(vr, p, monad_sets):
    verse_boundaries = from_cache(
        'verse_boundaries_{}_'.format(vr),
        lambda: passage_dbs[vr].executesql(u'''
select first_m, last_m from verse order by id
;
'''),
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
        (books, books_order, book_id, book_name) = from_cache('books_{}_'.format(vr), lambda: get_books(vr), None)
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

