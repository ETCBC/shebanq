#!/usr/bin/env python

from gluon.custom_import import track_changes

import collections
import json
import datetime
from urllib.parse import urlparse, urlunparse
from markdown import markdown

from render import (
    Verses,
    Verse,
    verse_simple,
    Viewsettings,
    legend,
    colorpicker,
    h_esc,
    get_request_val,
    get_fields,
    style,
    tp_labels,
    tab_views,
    tr_info,
    tr_labels,
    iid_encode,
    iid_decode,
    nt_statclass,
    booklangs,
    booknames,
    booktrans,
    from_cache,
    clear_cache,
    get_books,
)
from mql import mql
from get_db_config import emdros_versions


track_changes(True)

RESULT_PAGE_SIZE = 20
BLOCK_SIZE = 500
PUBLISH_FREEZE = datetime.timedelta(weeks=1)
PUBLISH_FREEZE_MSG = "1 week"
NULLDT = "____-__-__ __:__:__"


def books():
    session.forget(response)
    jsinit = """
var bookla = {bookla};
var booktrans = {booktrans};
var booklangs = {booklangs};
""".format(
        bookla=json.dumps(booknames["Hebrew"]["la"]),
        booktrans=json.dumps(booktrans),
        booklangs=json.dumps(booklangs["Hebrew"]),
    )
    return dict(jsinit=jsinit)


def text():
    session.forget(response)

    return dict(
        viewsettings=Viewsettings(cache, passage_dbs, URL, versions),
        colorpicker=colorpicker,
        legend=legend,
        tp_labels=tp_labels,
        tab_views=tab_views,
        tr_labels=tr_labels,
        tr_info=tr_info,
    )


def get_clause_atom_fmonad(vr):
    (books, books_order, book_id, book_name) = from_cache(
        cache, "books_{}_".format(vr), lambda: get_books(passage_dbs, vr), None
    )
    sql = """
select book_id, ca_num, first_m
from clause_atom
;
"""
    ca_data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
    clause_atom_first = {}
    for (bid, can, fm) in ca_data:
        bnm = book_name[bid]
        clause_atom_first.setdefault(bnm, {})[can] = fm
    return clause_atom_first


def get_clause_atoms(vr, bk, ch, vs):  # get clauseatoms for each verse
    clause_atoms = []
    ca_data = (
        passage_dbs[vr].executesql(
            """
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
""".format(
                bk, ch, vs
            )
        )
        if vr in passage_dbs
        else []
    )

    for (can,) in ca_data:
        clause_atoms.append(can)
    return clause_atoms


def get_blocks(
    vr,
):
    """get block info
    For each monad: to which block it belongs,
    for each block: book and chapter number of first word.
    Possibly there are gaps between books.
    """
    if vr not in passage_dbs:
        return ([], {})
    book_monads = passage_dbs[vr].executesql(
        """
select name, first_m, last_m from book
;
"""
    )
    chapter_monads = passage_dbs[vr].executesql(
        """
select chapter_num, first_m, last_m from chapter
;
"""
    )
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
        rep = (
            "{}.Z".format(cur_ch)
            if n == cur_ch_l
            else "{}.z".format(cur_ch)
            if round(10 * fraction) == 10
            else "{:0.1f}".format(cur_ch + fraction)
        )
        return (cur_ch, rep)

    while True:
        m += 1
        if m > cur_bk_l:
            size = round((float(cur_blk_size) / BLOCK_SIZE) * 100)
            blocks.append((cur_bk, cur_blk_f, get_curpos_info(m - 1), size))
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
            blocks.append((cur_bk, cur_blk_f, get_curpos_info(m - 1), 100))
            cur_blk_size = 0
        if m > cur_ch_l:
            cur_ch_index += 1
            if cur_ch_index >= len(chapter_monads):
                break
            else:
                (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
        if m < cur_bk_f:
            continue
        if m < cur_ch_f:
            continue
        if cur_blk_size == 0:
            cur_blk_f = get_curpos_info(m)
        block_mapping[m] = len(blocks)
        cur_blk_size += 1
    return (blocks, block_mapping)


def material():
    session.forget(response)
    mr = get_request_val("material", "", "mr")
    qw = get_request_val("material", "", "qw")
    vr = get_request_val("material", "", "version")
    bk = get_request_val("material", "", "book")
    ch = get_request_val("material", "", "chapter")
    tp = get_request_val("material", "", "tp")
    tr = get_request_val("material", "", "tr")
    lang = get_request_val("material", "", "lang")
    iidrep = get_request_val("material", "", "iid")
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
    page = get_request_val("material", "", "page")
    mrrep = "m" if mr == "m" else qw
    return from_cache(
        cache,
        "verses_{}_{}_{}_{}_{}_{}_{}_".format(
            vr,
            mrrep,
            bk if mr == "m" else iidrep,
            ch if mr == "m" else page,
            tp,
            tr,
            lang,
        ),
        lambda: material_c(vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang),
        None,
    )


def material_c(vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang):
    if mr == "m":
        (book, chapter) = getpassage()
        material = (
            Verses(passage_dbs, vr, mr, chapter=chapter["id"], tp=tp, tr=tr, lang=lang)
            if chapter
            else None
        )
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
    elif mr == "r":
        (iid, kw) = (None, None)
        if iidrep is not None:
            (iid, kw) = iid_decode(qw, iidrep)
        if iid is None:
            msg = "No {} selected".format(
                "query" if qw == "q" else "word" if qw == "w" else "note set"
            )
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
            (nmonads, monad_sets) = (
                load_q_hits(vr, iid)
                if qw == "q"
                else load_w_occs(vr, iid)
                if qw == "w"
                else load_n_notes(vr, iid, kw)
            )
            (nresults, npages, verses, monads) = get_pagination(vr, page, monad_sets)
            material = Verses(passage_dbs, vr, mr, verses, tp=tp, tr=tr, lang=lang)
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
    vr = get_request_val("material", "", "version")
    bk = get_request_val("material", "", "book")
    ch = get_request_val("material", "", "chapter")
    vs = get_request_val("material", "", "verse")
    tr = get_request_val("material", "", "tr")

    if request.extension == "json":
        return from_cache(
            cache,
            "versej_{}_{}_{}_{}_".format(vr, bk, ch, vs),
            lambda: verse_simple(passage_dbs, vr, bk, ch, vs),
            None,
        )

    if vs is None:
        return dict(good=False, msgs=msgs)
    return from_cache(
        cache,
        "verse_{}_{}_{}_{}_{}_".format(vr, bk, ch, vs, tr),
        lambda: verse_c(vr, bk, ch, vs, tr, msgs),
        None,
    )


def verse_c(vr, bk, ch, vs, tr, msgs):
    material = Verse(
        passage_dbs,
        vr,
        bk,
        ch,
        vs,
        xml=None,
        word_data=None,
        tp="txt_il",
        tr=tr,
        mr=None,
    )
    good = True
    if len(material.word_data) == 0:
        msgs.append(("error", "{} {}:{} does not exist".format(bk, ch, vs)))
        good = False
    result = dict(
        good=good,
        msgs=msgs,
        material=material,
    )
    return result


def cnotes():
    session.forget(response)
    myid = None
    msgs = []
    if auth.user:
        myid = auth.user.id
    logged_in = myid is not None
    vr = get_request_val("material", "", "version")
    bk = get_request_val("material", "", "book")
    ch = get_request_val("material", "", "chapter")
    vs = get_request_val("material", "", "verse")
    edit = check_bool("edit")
    save = check_bool("save")
    clause_atoms = from_cache(
        cache,
        "clause_atoms_{}_{}_{}_{}_".format(vr, bk, ch, vs),
        lambda: get_clause_atoms(vr, bk, ch, vs),
        None,
    )
    changed = False
    if save:
        changed = note_save(myid, vr, bk, ch, vs, clause_atoms, msgs)
    return cnotes_c(vr, bk, ch, vs, myid, clause_atoms, changed, msgs, logged_in, edit)


def cnotes_c(vr, bk, ch, vs, myid, clause_atoms, changed, msgs, logged_in, edit):
    condition = """note.is_shared = 'T' or note.is_published = 'T' """
    if myid is not None:
        condition += """ or note.created_by = {} """.format(myid)

    note_sql = """
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
""".format(
        cond=condition,
        vr=vr,
        bk=bk,
        ch=ch,
        vs=vs,
    )

    records = note_db.executesql(note_sql)
    users = {}
    nkey_index = {}
    notes_proto = collections.defaultdict(lambda: {})
    ca_users = collections.defaultdict(lambda: collections.OrderedDict())
    if myid is not None and edit:
        users[myid] = "me"
        for ca in clause_atoms:
            notes_proto[ca][myid] = [
                dict(uid=myid, nid=0, shared=True, pub=False, stat="o", kw="", ntxt="")
            ]
            ca_users[ca][myid] = None
    good = True
    if records is None:
        msgs.append(
            (
                "error",
                "Cannot lookup notes for {} {}:{} in version {}".format(bk, ch, vs, vr),
            )
        )
        good = False
    elif len(records) == 0:
        msgs.append(("warning", "No notes"))
    else:
        for (
            nid,
            uid,
            ufname,
            ulname,
            ca,
            shared,
            pub,
            pub_on,
            status,
            keywords,
            ntext,
        ) in records:
            if (myid is None or (uid != myid) or not edit) and uid not in users:
                users[uid] = "{} {}".format(ufname, ulname)
            if uid not in ca_users[ca]:
                ca_users[ca][uid] = None
            pub = pub == "T"
            shared = pub or shared == "T"
            ro = (
                myid is None
                or uid != myid
                or not edit
                or (
                    pub
                    and pub_on is not None
                    and (pub_on <= request.utcnow - PUBLISH_FREEZE)
                )
            )
            kws = keywords.strip().split()
            for k in kws:
                nkey_index["{} {}".format(uid, k)] = iid_encode("n", uid, kw=k)
            notes_proto.setdefault(ca, {}).setdefault(uid, []).append(
                dict(
                    uid=uid,
                    nid=nid,
                    ro=ro,
                    shared=shared,
                    pub=pub,
                    stat=status,
                    kw=keywords,
                    ntxt=ntext,
                )
            )
    notes = {}
    for ca in notes_proto:
        for uid in ca_users[ca]:
            notes.setdefault(ca, []).extend(notes_proto[ca][uid])

    return json.dumps(
        dict(
            good=good,
            changed=changed,
            msgs=msgs,
            users=users,
            notes=notes,
            nkey_index=nkey_index,
            logged_in=logged_in,
        )
    )


def note_save(myid, vr, bk, ch, vs, these_clause_atoms, msgs):
    if myid is None:
        msgs.append(("error", "You have to be logged in when you save notes"))
        return
    notes = (
        json.loads(request.post_vars.notes)
        if request.post_vars and request.post_vars.notes
        else []
    )
    (good, old_notes, upd_notes, new_notes, del_notes) = note_filter_notes(
        myid, notes, these_clause_atoms, msgs
    )

    updated = 0
    for nid in upd_notes:
        (shared, pub, stat, kw, ntxt) = upd_notes[nid]
        (o_shared, o_pub, o_stat, o_kw, o_ntxt) = old_notes[nid]
        extrafields = []
        if shared and not o_shared:
            extrafields.append(",\n\tshared_on = '{}'".format(request.utcnow))
        if not shared and o_shared:
            extrafields.append(",\n\tshared_on = null")
        if pub and not o_pub:
            extrafields.append(",\n\tpublished_on = '{}'".format(request.utcnow))
        if not pub and o_pub:
            extrafields.append(",\n\tpublished_on = null")
        shared = "'T'" if shared else "null"
        pub = "'T'" if pub else "null"
        stat = "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat
        update_sql = """
update note
    set modified_on = '{}',
    is_shared = {},
    is_published = {},
    status = '{}',
    keywords = '{}',
    ntext = '{}'{}
where id = {}
;
""".format(
            request.utcnow,
            shared,
            pub,
            stat,
            kw.replace("'", "''"),
            ntxt.replace("'", "''"),
            "".join(extrafields),
            nid,
        )
        note_db.executesql(update_sql)
        updated += 1
    if len(del_notes) > 0:
        del_sql = """
delete from note where id in ({})
;
""".format(
            ",".join(str(x) for x in del_notes)
        )
        note_db.executesql(del_sql)
    for canr in new_notes:
        (shared, pub, stat, kw, ntxt) = new_notes[canr]
        insert_sql = """
insert into note
(version, book, chapter, verse, clause_atom,
created_by, created_on, modified_on,
is_shared, shared_on, is_published, published_on,
status, keywords, ntext)
values
('{}', '{}', {}, {}, {}, {}, '{}', '{}', {}, {}, {}, {}, '{}', '{}', '{}')
;
""".format(
            vr,
            bk,
            ch,
            vs,
            canr,
            myid,
            request.utcnow,
            request.utcnow,
            "'T'" if shared else "null",
            "'{}'".format(request.utcnow) if shared else "null",
            "'T'" if pub else "null",
            "'{}'".format(request.utcnow) if pub else "null",
            "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat,
            kw.replace("'", "''"),
            ntxt.replace("'", "''"),
        )
        note_db.executesql(insert_sql)

    changed = False
    if len(del_notes) > 0:
        msgs.append(("special", "Deleted notes: {}".format(len(del_notes))))
    if updated > 0:
        msgs.append(("special", "Updated notes: {}".format(updated)))
    if len(new_notes) > 0:
        msgs.append(("special", "Added notes: {}".format(len(new_notes))))
    if len(del_notes) + len(new_notes) + updated == 0:
        msgs.append(("warning", "No changes"))
    else:
        changed = True
        clear_cache(cache, r"^items_n_{}_{}_{}_".format(vr, bk, ch))
        if len(new_notes):
            for kw in {new_notes[canr][3] for canr in new_notes}:
                clear_cache(
                    cache,
                    r"^verses_{}_{}_{}_".format(vr, "n", iid_encode("n", myid, kw=kw)),
                )
        if len(del_notes):
            for nid in del_notes:
                if nid in old_notes:
                    kw = old_notes[nid][3]
                    clear_cache(
                        cache,
                        r"^verses_{}_{}_{}_".format(
                            vr, "n", iid_encode("n", myid, kw=kw)
                        ),
                    )
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
        nid = int(fields["nid"])
        uid = int(fields["uid"])
        canr = int(fields["canr"])
        if uid != myid:
            other_user_notes.add(nid)
            good = False
            continue
        if canr not in these_clause_atoms:
            clause_errors.add(nid)
            good = False
            continue
        kw = "".join(" " + k + " " for k in fields["kw"].strip().split())
        ntxt = fields["ntxt"].strip()
        if kw == "" and ntxt == "":
            if nid == 0:
                emptynew += 1
            else:
                del_notes.add(nid)
            continue
        if nid != 0:
            upd_notes[nid] = (fields["shared"], fields["pub"], fields["stat"], kw, ntxt)
        else:
            new_notes[fields["canr"]] = (
                fields["shared"],
                fields["pub"],
                fields["stat"],
                kw,
                ntxt,
            )
    if len(upd_notes) > 0 or len(del_notes) > 0:
        old_sql = """
select id, created_by, is_shared, is_published, status, keywords, ntext
from note where id in ({})
;
""".format(
            ",".join(str(x) for x in (set(upd_notes.keys()) | del_notes))
        )
        cresult = note_db.executesql(old_sql)
        if cresult is not None:
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
                    if not shared:
                        shared = None
                    if not pub:
                        pub = None
                    if (
                        o_stat == stat
                        and o_kw == kw
                        and o_ntxt == ntxt
                        and o_shared == shared
                        and o_pub == pub
                    ):
                        same_notes.add(nid)
                        if nid not in del_notes:
                            remove = True
                if remove:
                    if nid in upd_notes:
                        del upd_notes[nid]
                    if nid in del_notes:
                        del_notes.remove(nid)
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
        msgs.append(
            ("error", "Notes of other users skipped: {}".format(len(other_user_notes)))
        )
    if len(missing_notes) > 0:
        msgs.append(("error", "Non-existing notes: {}".format(len(missing_notes))))
    if len(extra_notes) > 0:
        msgs.append(("error", "Notes not shown: {}".format(len(extra_notes))))
    if len(clause_errors) > 0:
        msgs.append(
            ("error", "Notes referring to wrong clause: {}".format(len(clause_errors)))
        )
    if len(same_notes) > 0:
        pass
        # msgs.append(('info', 'Unchanged notes: {}'.format(len(same_notes))))
    if emptynew > 0:
        pass
        # msgs.append(('info', 'Skipped empty new notes: {}'.format(emptynew)))
    return (good, old_notes, upd_notes, new_notes, del_notes)


def sidem():
    session.forget(response)
    vr = get_request_val("material", "", "version")
    qw = get_request_val("material", "", "qw")
    bk = get_request_val("material", "", "book")
    ch = get_request_val("material", "", "chapter")
    pub = get_request_val("highlights", qw, "pub") if qw != "w" else ""
    return from_cache(
        cache,
        "items_{}_{}_{}_{}_{}_".format(qw, vr, bk, ch, pub),
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
        if qw == "q":
            monad_sets = get_q_hits(vr, chapter, pub)
            side_items = groupq(vr, monad_sets)
        elif qw == "w":
            monad_sets = get_w_occs(vr, chapter)
            side_items = groupw(vr, monad_sets)
        elif qw == "n":
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
    session.forget(response)
    iidrep = get_request_val("material", "", "iid")
    request.vars["mr"] = "r"
    request.vars["qw"] = "q"
    if request.extension == "json":
        (authorized, msg) = item_access_read(iidrep=iidrep)
        if not authorized:
            result = dict(good=False, msg=[msg], data={})
        else:
            vr = get_request_val("material", "", "version")
            msgs = []
            (iid, kw) = iid_decode("q", iidrep)
            qrecord = get_query_info(
                False, iid, vr, msgs, with_ids=False, single_version=False, po=True
            )
            result = dict(good=qrecord is not None, msg=msgs, data=qrecord)
        return dict(data=json.dumps(result))
    else:
        request.vars["page"] = 1
    return text()


def word():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "w"
    request.vars["page"] = 1
    return text()


def note():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "n"
    request.vars["page"] = 1
    return text()


def csv(
    data,
):
    """converts an data structure of rows and fields into a csv string.
    With proper quotations and escapes
    """
    result = []
    if data is not None:
        for row in data:
            prow = [str(x) for x in row]
            trow = [
                '"{}"'.format(x.replace('"', '""')) if '"' in x or "," in x else x
                for x in prow
            ]
            result.append(
                (",".join(trow)).replace("\n", " ").replace("\r", " ")
            )  # no newlines in fields, it is impractical
    return "\n".join(result)


def item():
    """controller to produce a csv file of query results or lexeme occurrences
    Where fields are specified in the current legend
    """
    session.forget(response)
    vr = get_request_val("material", "", "version")
    iidrep = get_request_val("material", "", "iid")
    qw = get_request_val("material", "", "qw")
    tp = get_request_val("material", "", "tp")
    extra = get_request_val("rest", "", "extra")
    if extra:
        extra = "_" + extra
    if len(extra) > 64:
        extra = extra[0:64]
    (iid, kw) = iid_decode(qw, iidrep)
    iidrep2 = iid_decode(qw, iidrep, rsep=" ")
    filename = "{}_{}{}_{}{}.csv".format(
        vr, style[qw]["t"], iidrep2, tp_labels[tp], extra
    )
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        return dict(filename=filename, data=msg)
    hfields = get_fields(tp, qw=qw)
    if qw != "n":
        head_row = ["book", "chapter", "verse"] + [hf[1] for hf in hfields]
        (nmonads, monad_sets) = (
            load_q_hits(vr, iid) if qw == "q" else load_w_occs(vr, iid)
        )
        monads = flatten(monad_sets)
        data = []
        if len(monads):
            sql = """
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
""".format(
                hflist=", ".join("word.{}".format(hf[0]) for hf in hfields),
                monads=",".join(str(x) for x in monads),
            )
            data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
    else:
        head_row = ["book", "chapter", "verse"] + [hf[1] for hf in hfields]
        kw_sql = kw.replace("'", "''")
        myid = auth.user.id if auth.user is not None else None
        extra = """ or created_by = {} """.format(uid) if myid == iid else ""
        sql = """
select
    shebanq_note.note.book, shebanq_note.note.chapter, shebanq_note.note.verse,
    {hflist}
from shebanq_note.note
inner join book on shebanq_note.note.book = book.name
inner join clause_atom on clause_atom.ca_num = shebanq_note.note.clause_atom
    and clause_atom.book_id = book.id
where shebanq_note.note.keywords like '% {kw} %'
    and shebanq_note.note.version = '{vr}' and (shebanq_note.note.is_shared = 'T' {ex})
;
""".format(
            hflist=", ".join(hf[0] for hf in hfields),
            kw=kw_sql,
            vr=vr,
            ex=extra,
        )
        data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
    return dict(filename=filename, data=csv([head_row] + list(data)))


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    vr = get_request_val("material", "", "version")
    iidrep = get_request_val("material", "", "iid")
    qw = get_request_val("material", "", "qw")
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        result = get_chart(vr, [])
        result.update(qw=qw)
        return result
    return from_cache(
        cache,
        "chart_{}_{}_{}_".format(vr, qw, iidrep),
        lambda: chart_c(vr, qw, iidrep),
        None,
    )


def chart_c(vr, qw, iidrep):
    (iid, kw) = iid_decode(qw, iidrep)
    (nmonads, monad_sets) = (
        load_q_hits(vr, iid)
        if qw == "q"
        else load_w_occs(vr, iid)
        if qw == "w"
        else load_n_notes(vr, iid, kw)
    )
    result = get_chart(vr, monad_sets)
    result.update(qw=qw)
    return result


def sideqm():
    session.forget(response)
    iidrep = get_request_val("material", "", "iid")
    vr = get_request_val("material", "", "version")
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if authorized:
        msg = "fetching query"
    return dict(
        load=LOAD(
            "hebrew",
            "sideq",
            extension="load",
            vars=dict(mr="r", qw="q", version=vr, iid=iidrep),
            ajax=False,
            ajax_trap=True,
            target="querybody",
            content=msg,
        )
    )


def sidewm():
    session.forget(response)
    iidrep = get_request_val("material", "", "iid")
    vr = get_request_val("material", "", "version")
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if authorized:
        msg = "fetching word"
    return dict(
        load=LOAD(
            "hebrew",
            "sidew",
            extension="load",
            vars=dict(mr="r", qw="w", version=vr, iid=iidrep),
            ajax=False,
            ajax_trap=True,
            target="wordbody",
            content=msg,
        )
    )


def sidenm():
    session.forget(response)
    iidrep = get_request_val("material", "", "iid")
    vr = get_request_val("material", "", "version")
    msg = "Not a valid id {}".format(iidrep)
    if iidrep:
        msg = "fetching note set"
    return dict(
        load=LOAD(
            "hebrew",
            "siden",
            extension="load",
            vars=dict(mr="r", qw="n", version=vr, iid=iidrep),
            ajax=False,
            ajax_trap=True,
            target="notebody",
            content=msg,
        )
    )


def sideq():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "query", extension="", vars=request.vars))
    msgs = []
    iidrep = get_request_val("material", "", "iid")
    vr = get_request_val("material", "", "version")
    (iid, kw) = iid_decode("q", iidrep)
    (authorized, msg) = query_auth_read(iid)
    if iid == 0 or not authorized:
        msgs.append(("error", msg))
        return dict(
            writable=False,
            iidrep=iidrep,
            vr=vr,
            qr=dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
            oldeversions=set(emdros_versions[0:-1]),
        )
    q_record = get_query_info(
        auth.user is not None,
        iid,
        vr,
        msgs,
        with_ids=True,
        single_version=False,
        po=True,
    )
    if q_record is None:
        return dict(
            writable=True,
            iidrep=iidrep,
            vr=vr,
            qr=dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
            oldeversions=set(emdros_versions[0:-1]),
        )

    (authorized, msg) = query_auth_write(iid=iid)

    return dict(
        writable=authorized,
        iidrep=iidrep,
        vr=vr,
        qr=q_record,
        q=json.dumps(q_record),
        msgs=json.dumps(msgs),
        oldeversions=set(emdros_versions[0:-1]),
    )


def sidew():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "word", extension="", vars=request.vars))
    msgs = []
    vr = get_request_val("material", "", "version")
    iidrep = get_request_val("material", "", "iid")
    (iid, kw) = iid_decode("w", iidrep)
    (authorized, msg) = word_auth_read(vr, iid)
    if not authorized:
        msgs.append(("error", msg))
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
    if not request.ajax:
        redirect(URL("hebrew", "note", extension="", vars=request.vars))
    msgs = []
    vr = get_request_val("material", "", "version")
    iidrep = get_request_val("material", "", "iid")
    (iid, kw) = iid_decode("n", iidrep)
    if not iid:
        msg = "Not a valid id {}".format(iid)
        msgs.append(("error", msg))
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
    session.forget(response)
    viewsettings = Viewsettings(cache, passage_dbs, URL, versions)
    vr = get_request_val("material", "", "version", default=False)
    if not vr:
        vr = viewsettings.theversion()
    lan = get_request_val("rest", "", "lan")
    letter = get_request_val("rest", "", "letter")
    return from_cache(
        cache,
        "words_page_{}_{}_{}_".format(vr, lan, letter),
        lambda: words_page(viewsettings, vr, lan, letter),
        None,
    )


def queries():
    session.forget(response)
    msgs = []
    qid = check_id("goto", "q", "query", msgs)
    if qid is not None:
        if not query_auth_read(qid):
            qid = 0
    return dict(
        viewsettings=Viewsettings(cache, passage_dbs, URL, versions),
        qid=qid,
    )


def notes():
    session.forget(response)
    msgs = []
    nkid = check_id("goto", "n", "note", msgs)
    (may_upload, myid) = check_upload()
    return dict(
        viewsettings=Viewsettings(cache, passage_dbs, URL, versions),
        nkid=nkid,
        may_upload=may_upload,
        uid=myid,
    )


def check_upload(no_controller=True):
    myid = None
    may_upload = False
    if auth.user:
        myid = auth.user.id
    if myid:
        sql = """
select uid from uploaders where uid = {}
    """.format(
            myid
        )
        records = db.executesql(sql)
        may_upload = records is not None and len(records) == 1 and records[0][0] == myid
    return (may_upload, myid)


@auth.requires_login()
def note_upload():
    session.forget(response)
    msgs = []
    good = True
    uid = request.vars.uid
    (may_upload, myid) = check_upload()
    if may_upload and str(myid) == uid:
        good = load_notes(myid, request.vars.file, msgs)
    else:
        good = False
        msgs.append(["error", "you are not allowed to upload notes as csv files"])
    return dict(data=json.dumps(dict(msgs=msgs, good=good)))


def load_notes(uid, filetext, msgs):
    my_versions = set()
    book_info = {}
    for vr in versions:
        my_versions.add(vr)
        book_info[vr] = from_cache(
            cache, "books_{}_".format(vr), lambda: get_books(passage_dbs, vr), None
        )[0]
    normative_fields = "\t".join(
        """
        version
        book
        chapter
        verse
        clause_atom
        is_shared
        is_published
        status
        keywords
        ntext
    """.strip().split()
    )
    good = True
    fieldnames = normative_fields.split("\t")
    nfields = len(fieldnames)
    errors = {}
    allKeywords = set()
    allVersions = set()
    now = request.utcnow
    created_on = now
    modified_on = now

    nerrors = 0
    chunks = []
    chunksize = 100
    sqlhead = """
insert into note
({}, created_by, created_on, modified_on, shared_on, published_on, bulk) values
""".format(
        ", ".join(fieldnames)
    )

    this_chunk = []
    this_i = 0
    # for (i, linenl) in enumerate(str(filetext.value, encoding="utf8").split("\n")):
    # for (i, linenl) in enumerate(filetext.value.split("\n")):
    for (i, linenl) in enumerate(filetext.value.decode("utf8").split("\n")):
        line = linenl.rstrip()
        if line == "":
            continue
        if i == 0:
            if line != normative_fields:
                msgs.append(
                    [
                        "error",
                        "Wrong fields: {}. Required fields are {}".format(
                            line, normative_fields
                        ),
                    ]
                )
                good = False
                break
            continue
        fields = line.replace("'", "''").split("\t")
        if len(fields) != nfields:
            nerrors += 1
            errors.setdefault("wrong number of fields", []).append(i + 1)
            continue
        (
            version,
            book,
            chapter,
            verse,
            clause_atom,
            is_shared,
            is_published,
            status,
            keywords,
            ntext,
        ) = fields
        published_on = "NULL"
        shared_on = "NULL"
        if version not in my_versions:
            nerrors += 1
            errors.setdefault("unrecognized version", []).append(
                "{}:{}".format(i + 1, version)
            )
            continue
        books = book_info[version]
        if book not in books:
            nerrors += 1
            errors.setdefault("unrecognized book", []).append(
                "{}:{}".format(i + 1, book)
            )
            continue
        max_chapter = books[book]
        if not chapter.isdigit() or int(chapter) > max_chapter:
            nerrors += 1
            errors.setdefault("unrecognized chapter", []).append(
                "{}:{}".format(i + 1, chapter)
            )
            continue
        if not verse.isdigit() or int(verse) > 200:
            nerrors += 1
            errors.setdefault("unrecognized verse", []).append(
                "{}:{}".format(i + 1, verse)
            )
            continue
        if not clause_atom.isdigit() or int(clause_atom) > 100000:
            nerrors += 1
            errors.setdefault("unrecognized clause_atom", []).append(
                "{}:{}".format(i + 1, clause_atom)
            )
            continue
        if is_shared not in {"T", ""}:
            nerrors += 1
            errors.setdefault("unrecognized shared field", []).append(
                "{}:{}".format(i + 1, is_shared)
            )
            continue
        if is_published not in {"T", ""}:
            nerrors += 1
            errors.setdefault("unrecognized published field", []).append(
                "{}:{}".format(i + 1, is_published)
            )
            continue
        if status not in nt_statclass:
            nerrors += 1
            errors.setdefault("unrecognized status", []).append(
                "{}:{}".format(i + 1, status)
            )
            continue
        if len(keywords) >= 128:
            nerrors += 1
            errors.setdefault("keywords length over 128", []).append(
                "{}:{}".format(i + 1, len(keywords))
            )
            continue
        if len(ntext) >= 1024:
            nerrors += 1
            errors.setdefault("note text length over 1024", []).append(
                "{}:{}".format(i + 1, len(ntext))
            )
            continue
        if nerrors > 20:
            msgs.append(["error", "too many errors, aborting"])
            break
        if is_shared == "T":
            shared_on = "'{}'".format(now)
        if is_published == "T":
            published_on = "'{}'".format(now)
        keywordList = keywords.split()
        if len(keywordList) == 0:
            errors.setdefault("empty keyword", []).append(
                '{}:"{}"'.format(i + 1, keywords)
            )
            continue
        allKeywords |= set(keywordList)
        keywords = "".join(" {} ".format(x) for x in keywordList)
        allVersions.add(version)
        this_chunk.append(
            (
                "('{}','{}',{},{},{},'{}','{}','{}',"
                "'{}','{}',{},'{}','{}',{},{},'b')"
            ).format(
                version,
                book,
                chapter,
                verse,
                clause_atom,
                is_shared,
                is_published,
                status,
                keywords,
                ntext,
                uid,
                created_on,
                modified_on,
                shared_on,
                published_on,
            )
        )
        this_i += 1
        if this_i >= chunksize:
            chunks.append(this_chunk)
            this_chunk = []
            this_i = 0
    if len(this_chunk):
        chunks.append(this_chunk)

    # with open('/tmp/xxx.txt', 'w') as fh:
    #    for line in filetext.value:
    #        fh.write(line)
    if errors or nerrors:
        good = False
    else:
        whereVersion = "version in ('{}')".format("', '".join(allVersions))
        whereKeywords = " or ".join(
            " keywords like '% {} %' ".format(keyword) for keyword in keywordList
        )
        # first delete previously bulk uploaded notes by this author
        # and with these keywords and these versions
        delSql = """delete from note
        where bulk = 'b' and created_by = {} and {} and {};""".format(
            uid, whereVersion, whereKeywords
        )
        note_db.executesql(delSql)
        for chunk in chunks:
            sql = "{} {};".format(sqlhead, ",\n".join(chunk))
            note_db.executesql(sql)
        clear_cache(cache, r"^items_n_")
        for vr in my_versions:
            clear_cache(cache, r"^verses_{}_n_".format(vr))
    for msg in sorted(errors):
        msgs.append(
            ["error", "{}: {}".format(msg, ",".join(str(i) for i in errors[msg]))]
        )
    msgs.append(["good" if good else "error", "Done"])
    return True


def words_page(viewsettings, vr, lan=None, letter=None):
    (letters, words) = from_cache(
        cache, "words_data_{}_".format(vr), lambda: get_words_data(vr), None
    )
    version = viewsettings.versionstate()

    return dict(
        version=version,
        viewsettings=viewsettings,
        lan=lan,
        letter=letter,
        letters=letters,
        words=words.get(lan, {}).get(letter, []),
    )


# the query was:
#
#  select id, entry_heb, entryid_heb, lan, gloss from lexicon order by lan, entryid_heb
#
# normal sorting is not good enough: the pointed shin and sin turn out after the tav
# I will sort with key entryid_heb where every pointed shin/sin
# is preceded by an unpointed one.
# The unpointed one does turn up in the right place.


def heb_key(x):
    return x.replace("שׁ", "ששׁ").replace("שׂ", "ששׂ")


def get_words_data(vr):
    if vr not in passage_dbs:
        return ({}, {})
    ddata = sorted(
        passage_dbs[vr].executesql(
            """
select id, entry_heb, entryid_heb, lan, gloss from lexicon
;
"""
        ),
        key=lambda x: (x[3], heb_key(x[2])),
    )
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
    sql = """
select * from lexicon where id = '{}'
;
""".format(
        iid
    )
    w_record = dict(id=iid, versions={})
    for v in versions:
        records = passage_dbs[v].executesql(sql, as_dict=True)
        if records is None:
            msgs.append(
                ("error", "Cannot lookup word with id {} in version {}".format(iid, v))
            )
        elif len(records) == 0:
            msgs.append(("warning", "No word with id {} in version {}".format(iid, v)))
        else:
            w_record["versions"][v] = records[0]
    return w_record


def get_note_info(iidrep, vr, msgs):
    (iid, kw) = iid_decode("n", iidrep)
    if iid is None:
        return {}
    n_record = dict(id=iidrep, uid=iid, ufname="N?", ulname="N?", kw=kw, versions={})
    n_record["versions"] = count_n_notes(iid, kw)
    sql = """
select first_name, last_name from auth_user where id = '{}'
;
""".format(
        iid
    )
    uinfo = db.executesql(sql)
    if uinfo is not None and len(uinfo) > 0:
        n_record["ufname"] = uinfo[0][0]
        n_record["ulname"] = uinfo[0][1]
    return n_record


def get_query_info(
    show_private_fields, iid, vr, msgs, single_version=False, with_ids=True, po=False
):
    sqli = (
        """,
    query.created_by as uid,
    project.id as pid,
    organization.id as oid
"""
        if with_ids and po
        else ""
    )

    sqlx = (
        """,
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
"""
        if single_version
        else ""
    )

    sqlp = (
        """,
    project.name as pname,
    project.website as pwebsite,
    organization.name as oname,
    organization.website as owebsite
"""
        if po
        else ""
    )

    sqlb = (
        """,
    auth_user.email as uemail
"""
        if show_private_fields
        else """,
    'n.n@not.disclosed' as uemail
"""
    )

    sqlm = """
    query.id as id,
    query.name as name,
    query.description as description,
    query.created_on as created_on,
    query.modified_on as modified_on,
    query.is_shared as is_shared,
    query.shared_on as shared_on,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname
    {}{}{}{}
""".format(
        sqlb, sqli, sqlp, sqlx
    )

    sqlr = (
        """
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{}'
""".format(
            vr
        )
        if single_version
        else ""
    )

    sqlpr = (
        """
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
"""
        if po
        else ""
    )

    sqlc = (
        """
where query.id in ({})
""".format(
            ",".join(iid)
        )
        if single_version
        else """
where query.id = {}
""".format(
            iid
        )
    )

    sqlo = (
        """
order by auth_user.last_name, query.name
"""
        if single_version
        else ""
    )

    sql = """
select{} from query inner join auth_user on query.created_by = auth_user.id {}{}{}{}
;
""".format(
        sqlm, sqlr, sqlpr, sqlc, sqlo
    )
    records = db.executesql(sql, as_dict=True)
    if records is None:
        msgs.append(("error", "Cannot lookup query(ies)"))
        return None
    if single_version:
        for q_record in records:
            query_fields(vr, q_record, [], single_version=True)
        return records
    else:
        if len(records) == 0:
            msgs.append(("error", "No query with id {}".format(iid)))
            return None
        q_record = records[0]
        q_record["description_md"] = markdown(
            q_record["description"] or "", output_format="xhtml5"
        )
        sql = """
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
""".format(
            iid
        )
        recordx = db.executesql(sql, as_dict=True)
        query_fields(vr, q_record, recordx, single_version=False)
        return q_record


def pagelist(page, pages, spread):
    factor = 1
    filtered_pages = {1, page, pages}
    while factor <= pages:
        page_base = factor * int(page / factor)
        filtered_pages |= {
            page_base + int((i - spread / 2) * factor)
            for i in range(2 * int(spread / 2) + 1)
        }
        factor *= spread
    return sorted(i for i in filtered_pages if i > 0 and i <= pages)


RECENT_LIMIT = 50


def queriesr():
    session.forget(response)

    # The next query contains a clever idea from
    # http://stackoverflow.com/a/5657514
    # (http://stackoverflow.com/questions/5657446/mysql-query-max-group-by)
    # We want to find the most recent mql queries.
    # Queries may have multiple executions.
    # We want to have the queries with the most recent executions.
    # From such queries, we only want to have that one most recent executions.
    # This idea can be obtained by left outer joining the query_exe table
    # with itself (qe1 with qe2) # on the condition that the rows are combined
    # where qe1 and qe2 belong to the same query, and qe2 is more recent.
    # Rows in the combined table where qe2 is null, are such that qe1 is most recent.
    # This is the basic idea.
    # We then have to refine it: we only want shared queries.
    # That is an easy where condition on the final result.
    # We only want to have up-to-date queries.
    # So the join condition is not that qe2 is more recent,
    # but that qe2 is up-to-date and more recent.
    # And we need to add a where to express that qe1 is up to date.

    pqueryx_sql = """
select
    query.id as qid,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    query.name as qname,
    qe.executed_on as qexe,
    qe.version as qver
from query inner join
    (
        select qe1.query_id, qe1.executed_on, qe1.version
        from query_exe qe1
          left outer join query_exe qe2
            on (
                qe1.query_id = qe2.query_id and
                qe1.executed_on < qe2.executed_on and
                qe2.executed_on >= qe2.modified_on
            )
        where
            (qe1.executed_on is not null and qe1.executed_on >= qe1.modified_on) and
            qe2.query_id is null
    ) as qe
on qe.query_id = query.id
inner join auth_user on query.created_by = auth_user.id
where query.is_shared = 'T'
order by qe.executed_on desc, auth_user.last_name
limit {};
""".format(
        RECENT_LIMIT
    )

    pqueryx = db.executesql(pqueryx_sql)
    pqueries = []
    for (qid, ufname, ulname, qname, qexe, qver) in pqueryx:
        text = h_esc("{} {}: {}".format(ufname[0], ulname[0:9], qname[0:20]))
        title = h_esc("{} {}: {}".format(ufname, ulname, qname))
        pqueries.append(dict(id=qid, text=text, title=title, version=qver))

    return dict(data=json.dumps(dict(queries=pqueries, msgs=[], good=True)))


def query_tree():
    session.forget(response)
    myid = None
    if auth.user:
        myid = auth.user.id
    linfo = collections.defaultdict(lambda: {})

    def title_badge(lid, ltype, publ, good, num, tot):
        name = linfo[ltype][lid] if ltype is not None else "Shared Queries"
        nums = []
        if publ != 0:
            nums.append(
                '<span class="special fa fa-quote-right"> {}</span>'.format(publ)
            )
        if good != 0:
            nums.append('<span class="good fa fa-gears"> {}</span>'.format(good))
        badge = ""
        if len(nums) == 0:
            if tot == num:
                badge = '<span class="total">{}</span>'.format(", ".join(nums))
            else:
                badge = '{} of <span class="total">{}</span>'.format(
                    ", ".join(nums), tot
                )
        else:
            if tot == num:
                badge = '{} of <span class="total">{}</span>'.format(
                    ", ".join(nums), num
                )
            else:
                badge = '{} of {} of all <span class="total">{}</span>'.format(
                    ", ".join(nums), num, tot
                )
        rename = ""
        select = ""
        if ltype in {"o", "p"}:
            if myid is not None:
                if lid:
                    rename = '<a class="r_{}" lid="{}" href="#"></a>'.format(ltype, lid)
                select = '<a class="s_{} fa fa-lg" lid="{}" href="#"></a>'.format(
                    ltype, lid
                )
            else:
                if lid:
                    rename = '<a class="v_{}" lid="{}" href="#"></a>'.format(ltype, lid)
        return '{} <span n="1">{}</span><span class="brq">({})</span> {}'.format(
            select, h_esc(name), badge, rename
        )

    condition = (
        """
where query.is_shared = 'T'
"""
        if myid is None
        else """
where query.is_shared = 'T' or query.created_by = {}
""".format(
            myid
        )
    )

    pqueryx_sql = """
select
    query_exe.query_id,
    query_exe.version,
    query_exe.is_published,
    query_exe.published_on,
    query_exe.modified_on,
    query_exe.executed_on
from query_exe
inner join query on query.id = query_exe.query_id
{};
""".format(
        condition
    )

    pquery_sql = """
select
    query.id as qid,
    organization.name as oname, organization.id as oid,
    project.name as pname, project.id as pid,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname,
    auth_user.id as uid,
    query.name as qname, query.is_shared as is_shared
from query
inner join auth_user on query.created_by = auth_user.id
inner join project on query.project = project.id
inner join organization on query.organization = organization.id
{}
order by organization.name,
project.name,
auth_user.last_name,
auth_user.first_name,
query.name
;
""".format(
        condition
    )

    pquery = db.executesql(pquery_sql)
    pqueryx = db.executesql(pqueryx_sql)
    pqueries = collections.OrderedDict()
    for (qid, oname, oid, pname, pid, uname, uid, qname, qshared) in pquery:
        qsharedstatus = qshared == "T"
        qownstatus = uid == myid
        pqueries[qid] = {
            "": (oname, oid, pname, pid, uname, uid, qname, qsharedstatus, qownstatus),
            "publ": False,
            "good": False,
            "v": [4 for v in version_order],
        }
    for (qid, vr, qispub, qpub, qmod, qexe) in pqueryx:
        qinfo = pqueries[qid]
        qexestatus = None
        if qexe:
            qexestatus = qexe >= qmod
        qpubstatus = (
            False
            if qispub != "T"
            else None
            if qpub > request.utcnow - PUBLISH_FREEZE
            else True
        )
        qstatus = (
            1
            if qpubstatus
            else 2
            if qpubstatus is None
            else 3
            if qexestatus
            else 4
            if qexestatus is None
            else 5
        )
        qinfo["v"][version_index[vr]] = qstatus
        if qpubstatus or qpubstatus is None:
            qinfo["publ"] = True
        if qexestatus:
            qinfo["good"] = True

    porg_sql = """
select name, id from organization order by name
;
"""
    porg = db.executesql(porg_sql)

    pproj_sql = """
select name, id from project order by name
;
"""
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
    countu = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    )
    countu_publ = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    )
    countu_good = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    )
    countu_tot = collections.defaultdict(lambda: 0)
    count = 0
    count_publ = 0
    count_good = 0
    for qid in pqueries:
        pqinfo = pqueries[qid]
        (oname, oid, pname, pid, uname, uid, qname, qshared, qown) = pqinfo[""]
        qpubl = pqinfo["publ"]
        qgood = pqinfo["good"]
        countset["o"].add(oid)
        countset["p"].add(pid)
        countset["u"].add(uid)
        countset["q"].add(qid)
        linfo["o"][oid] = oname
        linfo["p"][pid] = pname
        linfo["u"][uid] = uname
        if qown:
            countset["m"].add(qid)
        if not qshared:
            countset["r"].add(qid)
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
        tree.setdefault(oid, collections.OrderedDict()).setdefault(
            pid, collections.OrderedDict()
        ).setdefault(uid, []).append(qid)
        count += 1
        counto[oid] += 1
        countp[oid][pid] += 1
        countu[oid][pid][uid] += 1
        counto_tot[oid] += 1
        countp_tot[pid] += 1
        countu_tot[uid] += 1

    linfo["o"][0] = "Projects without Queries"
    linfo["p"][0] = "New Project"
    linfo["u"][0] = ""
    linfo["q"] = pqueries
    counto[0] = 0
    countp[0][0] = 0
    for (oname, oid) in porg:
        if oid in linfo["o"]:
            continue
        countset["o"].add(oid)
        linfo["o"][oid] = oname
        tree[oid] = collections.OrderedDict()

    for (pname, pid) in pproj:
        if pid in linfo["p"]:
            continue
        countset["o"].add(0)
        countset["p"].add(pid)
        linfo["p"][pid] = pname
        tree.setdefault(0, collections.OrderedDict())[pid] = collections.OrderedDict()

    ccount = dict((x[0], len(x[1])) for x in countset.items())
    ccount["uid"] = myid
    title = title_badge(None, None, count_publ, count_good, count, count)
    dest = [dict(title="{}".format(title), folder=True, children=[], data=ccount)]
    curdest = dest[-1]["children"]
    cursource = tree
    for oid in cursource:
        onum = counto[oid]
        opubl = counto_publ[oid]
        ogood = counto_good[oid]
        otot = counto_tot[oid]
        otitle = title_badge(oid, "o", opubl, ogood, onum, otot)
        curdest.append(dict(title="{}".format(otitle), folder=True, children=[]))
        curodest = curdest[-1]["children"]
        curosource = cursource[oid]
        for pid in curosource:
            pnum = countp[oid][pid]
            ppubl = countp_publ[oid][pid]
            pgood = countp_good[oid][pid]
            ptot = countp_tot[pid]
            ptitle = title_badge(pid, "p", ppubl, pgood, pnum, ptot)
            curodest.append(dict(title="{}".format(ptitle), folder=True, children=[]))
            curpdest = curodest[-1]["children"]
            curpsource = curosource[pid]
            for uid in curpsource:
                unum = countu[oid][pid][uid]
                upubl = countu_publ[oid][pid][uid]
                ugood = countu_good[oid][pid][uid]
                utot = countu_tot[uid]
                utitle = title_badge(uid, "u", upubl, ugood, unum, utot)
                curpdest.append(
                    dict(title="{}".format(utitle), folder=True, children=[])
                )
                curudest = curpdest[-1]["children"]
                curusource = curpsource[uid]
                for qid in curusource:
                    pqinfo = linfo["q"][qid]
                    (oname, oid, pname, pid, uname, uid, qname, qshared, qown) = pqinfo[
                        ""
                    ]
                    qpubl = pqinfo["publ"]
                    qgood = pqinfo["good"]
                    qversions = pqinfo["v"]
                    rename = '<a class="{}_{}" lid="{}" href="#"></a>'.format(
                        "r" if qown else "v", "q", qid
                    )
                    curudest.append(
                        dict(
                            title=(
                                '{} <a class="q {} {}" n="1" qid="{}" href="#">'
                                '{}</a> <a class="md" href="#"></a> {}'
                            ).format(
                                " ".join(
                                    formatversion(
                                        "q", qid, v, qversions[version_index[v]]
                                    )
                                    for v in version_order
                                ),
                                "qmy" if qown else "",
                                "" if qshared else "qpriv",
                                iid_encode("q", qid),
                                h_esc(qname),
                                rename,
                            ),
                            key="q{}".format(qid),
                            folder=False,
                        )
                    )
    return dict(data=json.dumps(dest))


def note_tree():
    session.forget(response)
    myid = None
    if auth.user:
        myid = auth.user.id
    linfo = collections.defaultdict(lambda: {})

    def title_badge(lid, ltype, tot):
        name = linfo[ltype][lid] if ltype is not None else "Shared Notes"
        badge = ""
        if tot != 0:
            badge = '<span class="total special"> {}</span>'.format(tot)
        return '<span n="1">{}</span><span class="brn">({})</span>'.format(
            h_esc(name), badge
        )

    condition = (
        """
where note.is_shared = 'T'
"""
        if myid is None
        else """
where note.is_shared = 'T' or note.created_by = {}
""".format(
            myid
        )
    )

    pnote_sql = """
select
    count(note.id) as amount,
    note.version,
    note.keywords,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname, auth_user.id as uid
from note
inner join shebanq_web.auth_user on note.created_by = shebanq_web.auth_user.id
{}
group by auth_user.id, note.keywords, note.version
order by shebanq_web.auth_user.last_name,
shebanq_web.auth_user.first_name, note.keywords
;
""".format(
        condition
    )

    pnote = note_db.executesql(pnote_sql)
    pnotes = collections.OrderedDict()
    for (amount, nvr, kws, uname, uid) in pnote:
        for kw in set(kws.strip().split()):
            nkid = iid_encode("n", uid, kw=kw)
            if nkid not in pnotes:
                pnotes[nkid] = {"": (uname, uid, kw), "v": [0 for v in version_order]}
            pnotes[nkid]["v"][version_index[nvr]] = amount

    tree = collections.OrderedDict()
    countset = collections.defaultdict(lambda: set())
    countu = collections.defaultdict(lambda: 0)
    count = 0
    for nkid in pnotes:
        pninfo = pnotes[nkid]
        (uname, uid, nname) = pninfo[""]
        countset["u"].add(uid)
        countset["n"].add(nkid)
        linfo["u"][uid] = uname
        tree.setdefault(uid, []).append(nkid)
        count += 1
        countu[uid] += 1

    linfo["u"][0] = ""
    linfo["n"] = pnotes

    ccount = dict((x[0], len(x[1])) for x in countset.items())
    ccount["uid"] = myid
    title = title_badge(None, None, count)
    dest = [dict(title="{}".format(title), folder=True, children=[], data=ccount)]
    curdest = dest[-1]["children"]
    cursource = tree
    for uid in cursource:
        utot = countu[uid]
        utitle = title_badge(uid, "u", utot)
        curdest.append(dict(title="{}".format(utitle), folder=True, children=[]))
        curudest = curdest[-1]["children"]
        curusource = cursource[uid]
        for nkid in curusource:
            pninfo = linfo["n"][nkid]
            (uname, uid, nname) = pninfo[""]
            nversions = pninfo["v"]
            curudest.append(
                dict(
                    title=(
                        '{} <a class="n nt_kw" n="1" nkid="{}" href="#">'
                        '{}</a> <a class="md" href="#"></a>'
                    ).format(
                        " ".join(
                            formatversion("n", nkid, v, nversions[version_index[v]])
                            for v in version_order
                        ),
                        nkid,
                        h_esc(nname),
                    ),
                    key="n{}".format(nkid),
                    folder=False,
                ),
            )
    return dict(data=json.dumps(dest))


def formatversion(qw, lid, vr, st):
    if qw == "q":
        if st == 1:
            icon = "quote-right"
            cls = "special"
        elif st == 2:
            icon = "quote-right"
            cls = ""
        elif st == 3:
            icon = "gears"
            cls = "good"
        elif st == 4:
            icon = "circle-o"
            cls = "warning"
        elif st == 5:
            icon = "clock-o"
            cls = "error"
        return '<a href="#" class="ctrl br{} {} fa fa-{}" {}id="{}" v="{}"></a>'.format(
            qw, cls, icon, qw, lid, vr
        )
    else:
        return '<a href="#" class="ctrl br{}" nkid="{}" v="{}">{}</a>'.format(
            qw, lid, vr, st if st else "-"
        )


tps = dict(
    o=("organization", "organization"), p=("project", "project"), q=("query", "query")
)


def check_unique(tp, lid, val, myid, msgs):
    result = False
    (label, table) = tps[tp]
    for x in [1]:
        if tp == "q":
            check_sql = """
select id from query where name = '{}' and query.created_by = {}
;
""".format(
                val, myid
            )
        else:
            check_sql = """
select id from {} where name = '{}'
;
""".format(
                table, val
            )
        try:
            ids = db.executesql(check_sql)
        except Exception:
            msgs.append(
                ("error", "cannot check the unicity of {} as {}!".format(val, label))
            )
            break
        if len(ids) and (lid == 0 or ids[0][0] != int(lid)):
            msgs.append(("error", "the {} name is already taken!".format(label)))
            break
        result = True
    return result


def check_name(tp, lid, myid, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 64:
            msgs.append(
                (
                    "error",
                    "{label} name is longer than 64 characters!".format(label=label),
                )
            )
            break
        val = val.strip()
        if val == "":
            msgs.append(
                (
                    "error",
                    "{label} name consists completely of white space!".format(
                        label=label
                    ),
                )
            )
            break
        val = val.replace("'", "''")
        if not check_unique(tp, lid, val, myid, msgs):
            break
        result = val
    return result


def check_description(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 8192:
            msgs.append(
                (
                    "error",
                    "{label} description is longer than 8192 characters!".format(
                        label=label
                    ),
                )
            )
            break
        result = val.replace("'", "''")
    return result


def check_mql(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 8192:
            msgs.append(
                (
                    "error",
                    "{label} mql is longer than 8192 characters!".format(label=label),
                )
            )
            break
        result = val.replace("'", "''")
    return result


def check_published(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 10 or (len(val) > 0 and not val.isalnum()):
            msgs.append(
                (
                    "error",
                    "{} published status has an invalid value {}".format(label, val),
                )
            )
            break
        result = "T" if val == "T" else ""
    return result


def check_website(tp, val, msgs):
    label = tps[tp][0]
    result = None
    for x in [1]:
        if len(val) > 512:
            msgs.append(
                (
                    "error",
                    "{label} website is longer than 512 characters!".format(
                        label=label
                    ),
                )
            )
            break
        val = val.strip()
        if val == "":
            msgs.append(
                (
                    "error",
                    "{label} website consists completely of white space!".format(
                        label=label
                    ),
                )
            )
            break
        try:
            url_comps = urlparse(val)
        except ValueError:
            msgs.append(
                ("error", "invalid syntax in {label} website !".format(label=label))
            )
            break
        scheme = url_comps.scheme
        if scheme not in {"http", "https"}:
            msgs.append(
                (
                    "error",
                    "{label} website does not start with http(s)://".format(
                        label=label
                    ),
                )
            )
            break
        netloc = url_comps.netloc
        if "." not in netloc:
            msgs.append(("error", "no location in {label} website".format(label=label)))
            break
        result = urlunparse(url_comps).replace("'", "''")
    return result


def check_int(var, label, msgs):
    val = request.vars[var]
    if val is None:
        msgs.append(("error", "No {} number given".format(label)))
        return None
    if len(val) > 10 or not val.isdigit():
        msgs.append(("error", "Not a valid {} verse".format(label)))
        return None
    return int(val)


def check_bool(var):
    val = request.vars[var]
    if (
        val is None
        or len(val) > 10
        or not val.isalpha()
        or val not in {"true", "false"}
        or val == "false"
    ):
        return False
    return True


def check_id(var, tp, label, msgs, valrep=None):
    if valrep is None:
        valrep = request.vars[var]
    if valrep is None:
        msgs.append(("error", "No {} id given".format(label)))
        return None
    if tp in {"w", "q", "n"}:
        (val, kw) = iid_decode(tp, valrep)
    else:
        val = valrep
        if len(valrep) > 10 or not valrep.isdigit():
            msgs.append(("error", "Not a valid {} id".format(label)))
            return None
        val = int(valrep)
    if tp == "n":
        return valrep
    return val


def check_rel(tp, val, msgs):
    (label, table) = tps[tp]
    result = None
    for x in [1]:
        check_sql = """
select count(*) as occurs from {} where id = {}
;
""".format(
            table, val
        )
        try:
            occurs = db.executesql(check_sql)[0][0]
        except Exception:
            msgs.append(
                (
                    "error",
                    "cannot check the occurrence of {} id {}!".format(label, val),
                )
            )
            break
        if not occurs:
            if val == 0:
                msgs.append(("error", "No {} chosen!".format(label)))
            else:
                msgs.append(("error", "There is no {} {}!".format(label, val)))
            break
        result = val
    return result


def record():
    session.forget(response)
    msgs = []
    record = {}
    orecord = {}
    precord = {}
    good = False
    ogood = False
    pgood = False
    myid = auth.user.id if auth.user is not None else None
    for x in [1]:
        tp = request.vars.tp
        if tp not in tps:
            msgs.append(("error", "unknown type {}!".format(tp)))
            break
        (label, table) = tps[tp]
        lid = check_id("lid", tp, label, msgs)
        upd = request.vars.upd
        if lid is None:
            break
        if upd not in {"true", "false"}:
            msgs.append(("error", "invalid instruction {}!".format(upd)))
            break
        upd = True if upd == "true" else False
        if upd and not myid:
            msgs.append(("error", "for updating you have to be logged in!"))
            break
        fields = ["name"]
        if tp == "q":
            fields.append("organization")
            fields.append("project")
        else:
            fields.append("website")
        if upd:
            (authorized, msg) = (
                query_auth_write(lid) if tp == "q" else auth_write(label)
            )
        else:
            (authorized, msg) = query_auth_read(lid) if tp == "q" else auth_read(label)
        if not authorized:
            msgs.append(("error", msg))
            break
        if upd:
            fvalues = None
            if tp == "q":
                subfields = ["name", "website"]
                fvalues = [request.vars.name]
                do_new_o = request.vars.do_new_o
                do_new_p = request.vars.do_new_p
                if do_new_o not in {"true", "false"}:
                    msgs.append(
                        (
                            "error",
                            "invalid instruction for organization {}!".format(do_new_o),
                        )
                    )
                    break
                do_new_o = do_new_o == "true"
                if do_new_p not in {"true", "false"}:
                    msgs.append(
                        (
                            "error",
                            "invalid instruction for project {}!".format(do_new_p),
                        )
                    )
                    break
                do_new_p = do_new_p == "true"
                ogood = True
                if do_new_o:
                    (ogood, oid) = upd_record(
                        "o",
                        0,
                        myid,
                        subfields,
                        msgs,
                        fvalues=[request.vars.oname, request.vars.owebsite],
                    )
                    if ogood:
                        orecord = dict(
                            id=oid,
                            name=request.vars.oname,
                            website=request.vars.owebsite,
                        )
                else:
                    oid = check_id("oid", "o", tps["o"][0], msgs)
                pgood = True
                if do_new_p:
                    (pgood, pid) = upd_record(
                        "p",
                        0,
                        myid,
                        subfields,
                        msgs,
                        fvalues=[request.vars.pname, request.vars.pwebsite],
                    )
                    if pgood:
                        precord = dict(
                            id=pid,
                            name=request.vars.pname,
                            website=request.vars.pwebsite,
                        )
                else:
                    pid = check_id("pid", "p", tps["o"][0], msgs)
                if not ogood or not pgood:
                    break
                if oid is None or pid is None:
                    break
                fvalues.extend([oid, pid])
            (good, new_lid) = upd_record(tp, lid, myid, fields, msgs, fvalues=fvalues)
            if not good:
                break
            lid = new_lid
        else:
            good = True
        dbrecord = None
        if tp == "q":
            if lid == 0:
                dbrecord = [0, "", 0, "", "", 0, "", ""]
            else:
                dbrecord = db.executesql(
                    """
select
query.id as id,
query.name as name,
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
""".format(
                        lid
                    ),
                    as_dict=True,
                )
        else:
            if lid == 0:
                dbrecord = [0, "", ""]
            else:
                dbrecord = db.executesql(
                    """
select {} from {} where id = {}
;
""".format(
                        ",".join(fields), table, lid
                    ),
                    as_dict=True,
                )
        if not dbrecord:
            msgs.append(("error", "No {} with id {}".format(label, lid)))
            break
        record = dbrecord[0]
    return dict(
        data=json.dumps(
            dict(
                record=record,
                orecord=orecord,
                precord=precord,
                msgs=msgs,
                good=good,
                ogood=ogood,
                pgood=pgood,
            )
        )
    )


def upd_record(tp, lid, myid, fields, msgs, fvalues=None):
    updrecord = {}
    good = False
    (label, table) = tps[tp]
    use_values = {}
    for i in range(len(fields)):
        field = fields[i]
        value = fvalues[i] if fvalues is not None else request.vars[field]
        use_values[field] = value

    for x in [1]:
        valsql = check_name(
            # tp, lid, myid, str(use_values["name"], encoding="utf-8"), msgs
            tp,
            lid,
            myid,
            use_values["name"],
            msgs,
        )
        if valsql is None:
            break
        updrecord["name"] = valsql
        if tp == "q":
            val = check_id(
                "oid", "o", tps["o"][0], msgs, valrep=str(use_values["organization"])
            )
            if val is None:
                break
            valsql = check_rel("o", val, msgs)
            if valsql is None:
                break
            updrecord["organization"] = valsql
            val = check_id(
                "pid", "p", tps["p"][0], msgs, valrep=str(use_values["project"])
            )
            valsql = check_rel("p", val, msgs)
            if valsql is None:
                break
            updrecord["project"] = valsql
            fld = "modified_on"
            updrecord[fld] = request.utcnow
            fields.append(fld)
            if lid == 0:
                fld = "created_on"
                updrecord[fld] = request.utcnow
                fields.append(fld)
                fld = "created_by"
                updrecord[fld] = myid
                fields.append(fld)
        else:
            valsql = check_website(tp, use_values["website"], msgs)
            if valsql is None:
                break
            updrecord["website"] = valsql
        good = True
    if good:
        if lid:
            fieldvals = [" {} = '{}'".format(f, updrecord[f]) for f in fields]
            sql = """update {} set{} where id = {};""".format(
                table, ",".join(fieldvals), lid
            )
            thismsg = "updated"
        else:
            fieldvals = ["'{}'".format(updrecord[f]) for f in fields]
            sql = """
insert into {} ({}) values ({})
;
""".format(
                table, ",".join(fields), ",".join(fieldvals)
            )
            thismsg = "{} added".format(label)
        db.executesql(sql)
        if lid == 0:
            lid = db.executesql(
                """
select last_insert_id() as x
;
"""
            )[0][0]

        msgs.append(("good", thismsg))
    return (good, lid)


def field():
    session.forget(response)
    msgs = []
    good = False
    mod_dates = {}
    mod_cls = ""
    extra = {}
    for x in [1]:
        qid = check_id("qid", "q", "query", msgs)
        if qid is None:
            break
        fname = request.vars.fname
        val = request.vars.val
        vr = request.vars.version
        if fname is None or fname not in {"is_shared", "is_published"}:
            msgs.append("error", "Illegal field name {}")
            break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(("error", msg))
            break
        (good, mod_dates, mod_cls, extra) = upd_field(vr, qid, fname, val, msgs)
    return dict(
        data=json.dumps(
            dict(
                msgs=msgs, good=good, mod_dates=mod_dates, mod_cls=mod_cls, extra=extra
            )
        )
    )


def upd_shared(myid, qid, valsql, msgs):
    mod_date = None
    mod_date_fld = "shared_on"
    table = "query"
    fname = "is_shared"
    clear_cache(cache, r"^items_q_")
    fieldval = " {} = '{}'".format(fname, valsql)
    mod_date = request.utcnow.replace(microsecond=0) if valsql == "T" else None
    mod_date_sql = "null" if mod_date is None else "'{}'".format(mod_date)
    fieldval += ", {} = {} ".format(mod_date_fld, mod_date_sql)
    sql = """
update {} set{} where id = {}
;
""".format(
        table, fieldval, qid
    )
    db.executesql(sql)
    thismsg = "modified"
    thismsg = "shared" if valsql == "T" else "UNshared"
    msgs.append(("good", thismsg))
    return (mod_date_fld, str(mod_date) if mod_date else NULLDT)


def upd_published(myid, vr, qid, valsql, msgs):
    mod_date = None
    mod_date_fld = "published_on"
    table = "query_exe"
    fname = "is_published"
    clear_cache(cache, r"^items_q_{}_".format(vr))
    verify_version(qid, vr)
    fieldval = " {} = '{}'".format(fname, valsql)
    mod_date = request.utcnow.replace(microsecond=0) if valsql == "T" else None
    mod_date_sql = "null" if mod_date is None else "'{}'".format(mod_date)
    fieldval += ", {} = {} ".format(mod_date_fld, mod_date_sql)
    sql = """
update {} set{} where query_id = {} and version = '{}'
;
""".format(
        table, fieldval, qid, vr
    )
    db.executesql(sql)
    thismsg = "modified"
    thismsg = "published" if valsql == "T" else "UNpublished"
    msgs.append(("good", thismsg))
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
        # valsql = check_published("q", str(val, encoding="utf-8"), msgs)
        valsql = check_published("q", val, msgs)
        if valsql is None:
            break
        if fname == "is_shared" and valsql == "":
            sql = """
select count(*) from query_exe where query_id = {} and is_published = 'T'
;
""".format(
                qid
            )
            pv = db.executesql(sql)
            has_public_versions = pv is not None and len(pv) == 1 and pv[0][0] > 0
            if has_public_versions:
                msgs.append(
                    (
                        "error",
                        (
                            "You cannot UNshare this query because there is"
                            "a published execution record"
                        ),
                    )
                )
                break
        if fname == "is_published":
            mod_cls["#is_pub_ro"] = "fa-{}".format(
                "check" if valsql == "T" else "close"
            )
            mod_cls['div[version="{}"]'.format(vr)] = (
                "published" if valsql == "T" else "unpublished"
            )
            extra["execq"] = ("show", valsql != "T")
            if valsql == "T":
                sql = """
select executed_on, modified_on as xmodified_on
from query_exe where query_id = {} and version = '{}'
;
""".format(
                    qid, vr
                )
                pv = db.executesql(sql, as_dict=True)
                if pv is None or len(pv) != 1:
                    msgs.append(
                        (
                            "error",
                            "cannot determine whether query results are up to date",
                        )
                    )
                    break
                uptodate = qstatus(pv[0])
                if uptodate != "good":
                    msgs.append(
                        (
                            "error",
                            "You can only publish if the query results are up to date",
                        )
                    )
                    break
                sql = """
select is_shared from query where id = {}
;
""".format(
                    qid
                )
                pv = db.executesql(sql)
                is_shared = pv is not None and len(pv) == 1 and pv[0][0] == "T"
                if not is_shared:
                    (mod_date_fld, mod_date) = upd_shared(myid, qid, "T", msgs)
                    mod_dates[mod_date_fld] = mod_date
                    extra["is_shared"] = ("checked", True)
            else:
                sql = """
select published_on from query_exe where query_id = {} and version = '{}'
;
""".format(
                    qid, vr
                )
                pv = db.executesql(sql)
                pdate_ok = (
                    pv is None
                    or len(pv) != 1
                    or pv[0][0] is None
                    or pv[0][0] > request.utcnow - PUBLISH_FREEZE
                )
                if not pdate_ok:
                    msgs.append(
                        (
                            "error",
                            (
                                "You cannot UNpublish this query because"
                                "it has been published more than {} ago"
                            ).format(PUBLISH_FREEZE_MSG),
                        )
                    )
                    break

        good = True

    if good:
        if fname == "is_shared":
            (mod_date_fld, mod_date) = upd_shared(myid, qid, valsql, msgs)
        else:
            (mod_date_fld, mod_date) = upd_published(myid, vr, qid, valsql, msgs)
        mod_dates[mod_date_fld] = mod_date
    return (good, mod_dates, mod_cls, extra)


def verify_version(qid, vr):
    exist_version = db.executesql(
        """
select id from query_exe where version = '{}' and query_id = {}
;
""".format(
            vr, qid
        )
    )
    if exist_version is None or len(exist_version) == 0:
        db.executesql(
            """
insert into query_exe (id, version, query_id) values (null, '{}', {})
;
""".format(
                vr, qid
            )
        )


def fields():
    session.forget(response)
    msgs = []
    good = False
    myid = auth.user.id if auth.user is not None else None
    flds = {}
    fldx = {}
    vr = request.vars.version
    q_record = {}
    for x in [1]:
        qid = check_id("qid", "q", "query", msgs)
        if qid is None:
            break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(("error", msg))
            break

        verify_version(qid, vr)
        oldrecord = db.executesql(
            """
select
    query.name as name,
    query.description as description,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{}'
where query.id = {}
;
""".format(
                vr, qid
            ),
            as_dict=True,
        )
        if oldrecord is None or len(oldrecord) == 0:
            msgs.append(("error", "No query with id {}".format(qid)))
            break
        oldvals = oldrecord[0]
        is_published = oldvals["is_published"] == "T"
        if not is_published:
            # newname = str(request.vars.name, encoding="utf-8")
            newname = request.vars.name
            if oldvals["name"] != newname:
                valsql = check_name("q", qid, myid, newname, msgs)
                if valsql is None:
                    break
                flds["name"] = valsql
                flds["modified_on"] = request.utcnow
            newmql = request.vars.mql
            # newmql_u = str(newmql, encoding="utf-8")
            newmql_u = newmql
            if oldvals["mql"] != newmql_u:
                msgs.append(("warning", "query body modified"))
                valsql = check_mql("q", newmql_u, msgs)
                if valsql is None:
                    break
                fldx["mql"] = valsql
                fldx["modified_on"] = request.utcnow
            else:
                msgs.append(("good", "same query body"))
        else:
            msgs.append(
                (
                    "warning",
                    (
                        "only the description can been saved"
                        "because this is a published query execution"
                    ),
                )
            )
        # newdesc = str(request.vars.description, encoding="utf-8")
        newdesc = request.vars.description
        if oldvals["description"] != newdesc:
            valsql = check_description("q", newdesc, msgs)
            if valsql is None:
                break
            flds["description"] = valsql
            flds["modified_on"] = request.utcnow
        good = True
    if good:
        execute = not is_published and request.vars.execute
        xgood = True
        if execute == "true":
            (xgood, limit_exceeded, nresults, xmonads, this_msgs, eversion) = mql(
                vr, newmql
            )
            if xgood and not limit_exceeded:
                store_monad_sets(vr, qid, xmonads)
                fldx["executed_on"] = request.utcnow
                fldx["eversion"] = eversion
                nresultmonads = count_monads(xmonads)
                fldx["results"] = nresults
                fldx["resultmonads"] = nresultmonads
                msgs.append(("good", "Query executed"))
            else:
                store_monad_sets(vr, qid, [])
            msgs.extend(this_msgs)
        if len(flds):
            sql = """
update {} set{} where id = {}
;
""".format(
                "query",
                ", ".join(
                    " {} = '{}'".format(f, flds[f]) for f in flds if f != "status"
                ),
                qid,
            )
            db.executesql(sql)
            clear_cache(cache, r"^items_q_")
        if len(fldx):
            sql = """
update {} set{} where query_id = {} and version = '{}'
;
""".format(
                "query_exe",
                ", ".join(
                    " {} = '{}'".format(f, fldx[f]) for f in fldx if f != "status"
                ),
                qid,
                vr,
            )
            db.executesql(sql)
            clear_cache(cache, r"^items_q_{}_".format(vr))
        q_record = get_query_info(
            auth.user is not None,
            qid,
            vr,
            msgs,
            with_ids=False,
            single_version=False,
            po=True,
        )

    oldeversions = dict((x, 1) for x in emdros_versions[0:-1])
    return dict(
        data=json.dumps(
            dict(msgs=msgs, good=good and xgood, q=q_record, oldeversions=oldeversions)
        )
    )


def datetime_str(fields):
    for f in (
        "created_on",
        "modified_on",
        "shared_on",
        "xmodified_on",
        "executed_on",
        "published_on",
    ):
        if f in fields:
            ov = fields[f]
            fields[f] = str(ov) if ov else NULLDT
    for f in ("is_shared", "is_published"):
        if f in fields:
            fields[f] = fields[f] == "T"


def qstatus(qx_record):
    if not qx_record["executed_on"]:
        return "warning"
    if qx_record["executed_on"] < qx_record["xmodified_on"]:
        return "error"
    return "good"


def query_fields(vr, q_record, recordx, single_version=False):
    datetime_str(q_record)
    if not single_version:
        q_record["versions"] = dict(
            (
                v,
                dict(
                    xid=None,
                    mql=None,
                    status="warning",
                    is_published=None,
                    results=None,
                    resultmonads=None,
                    xmodified_on=None,
                    executed_on=None,
                    eversion=None,
                    published_on=None,
                ),
            )
            for v in versions
        )
        for rx in recordx:
            vx = rx["version"]
            if vx not in versions:
                continue
            dest = q_record["versions"][vx]
            dest.update(rx)
            dest["status"] = qstatus(dest)
            datetime_str(dest)


def flatten(msets):
    result = set()
    for (b, e) in msets:
        for m in range(b, e + 1):
            result.add(m)
    return list(sorted(result))


def getpassage(no_controller=True):
    vr = get_request_val("material", "", "version")
    bookname = get_request_val("material", "", "book")
    chapternum = get_request_val("material", "", "chapter")
    if bookname is None or chapternum is None or vr not in passage_dbs:
        return ({}, {})
    bookrecords = passage_dbs[vr].executesql(
        """
select * from book where name = '{}'
;
""".format(
            bookname
        ),
        as_dict=True,
    )
    book = bookrecords[0] if bookrecords else {}
    if book and "id" in book:
        chapterrecords = passage_dbs[vr].executesql(
            """
select * from chapter where chapter_num = {} and book_id = {}
;
""".format(
                chapternum, book["id"]
            ),
            as_dict=True,
        )
        chapter = chapterrecords[0] if chapterrecords else {}
    else:
        chapter = {}
    return (book, chapter)


def groupq(vr, input):
    monads = collections.defaultdict(lambda: set())
    for (qid, b, e) in input:
        monads[qid] |= set(range(b, e + 1))
    r = []
    if len(monads):
        msgs = []
        queryrecords = get_query_info(
            False,
            (str(q) for q in monads),
            vr,
            msgs,
            with_ids=False,
            single_version=True,
            po=False,
        )
        for q in queryrecords:
            r.append({"item": q, "monads": json.dumps(sorted(list(monads[q["id"]])))})
    return r


# select * from lexicon where id in ({}) order by entryid_heb
# again: modify the sorting because of shin and sin
# (see comments to function words_page)


def groupw(vr, input):
    if vr not in passage_dbs:
        return []
    wids = collections.defaultdict(lambda: [])
    for x in input:
        wids[x[1]].append(x[0])
    r = []
    if len(wids):
        wsql = """
select * from lexicon where id in ({})
;
""".format(
            ",".join("'{}'".format(str(x)) for x in wids)
        )
        wordrecords = sorted(
            passage_dbs[vr].executesql(wsql, as_dict=True),
            key=lambda x: heb_key(x["entryid_heb"]),
        )
        for w in wordrecords:
            r.append({"item": w, "monads": json.dumps(wids[w["id"]])})
    return r


def get_notes(vr, book, chapter, pub):
    bk = book["name"]
    ch = chapter["chapter_num"]
    if pub == "x":
        pubv = ""
    else:
        pubv = " and is_published = 'T'"
    sql = """
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
""".format(
        vr, bk, ch, pubv
    )
    records = note_db.executesql(sql)
    user = {}
    npub = collections.Counter()
    nnotes = collections.Counter()
    nverses = {}
    for (uid, ufname, ulname, kw, v, pub) in records:
        if uid not in user:
            user[uid] = (ufname, ulname)
        for k in set(kw.strip().split()):
            if pub == "T":
                npub[(uid, k)] += 1
            nnotes[(uid, k)] += 1
            nverses.setdefault((uid, k), set()).add(v)
    r = []
    for (uid, k) in nnotes:
        (ufname, ulname) = user[uid]
        this_npub = npub[(uid, k)]
        this_nnotes = nnotes[(uid, k)]
        this_nverses = len(nverses[(uid, k)])
        r.append(
            {
                "item": dict(
                    id=iid_encode("n", uid, k),
                    ufname=ufname,
                    ulname=ulname,
                    kw=k,
                    is_published=this_npub > 0,
                    nnotes=this_nnotes,
                    nverses=this_nverses,
                ),
                "monads": json.dumps([]),
            }
        )
    return r


def get_q_hits(vr, chapter, pub):
    if pub == "x":
        pubv = ""
        pubx = """inner join query on
        query.id = query_exe.query_id and query.is_shared = 'T'"""
    else:
        pubv = " and query_exe.is_published = 'T'"
        pubx = ""

    q_hits_chapter = """
select DISTINCT
    query_exe.query_id as query_id,
    GREATEST(first_m, {chapter_first_m}) as first_m,
    LEAST(last_m, {chapter_last_m}) as last_m
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and
    query_exe.executed_on >= query_exe.modified_on {pubv}
{pubx}
where
    (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    ({chapter_first_m} BETWEEN first_m AND last_m)
;
""".format(
        chapter_last_m=chapter["last_m"],
        chapter_first_m=chapter["first_m"],
        vr=vr,
        pubv=pubv,
        pubx=pubx,
    )
    # print(q_hits_chapter)
    return db.executesql(q_hits_chapter)


def get_w_occs(vr, chapter):
    return (
        passage_dbs[vr].executesql(
            """
select anchor, lexicon_id
from word_verse
where anchor BETWEEN {chapter_first_m} AND {chapter_last_m}
;
""".format(
                chapter_last_m=chapter["last_m"],
                chapter_first_m=chapter["first_m"],
            )
        )
        if vr in passage_dbs
        else []
    )


def to_ascii(x):
    return x.encode("ascii", "replace")


def item_access_read(iidrep=get_request_val("material", "", "iid")):
    mr = get_request_val("material", "", "mr")
    qw = get_request_val("material", "", "qw")
    if mr == "m":
        return (True, "")
    if qw == "w":
        return (True, "")
    if qw == "n":
        return (True, "")
    if qw == "q":
        if iidrep is not None:
            (iid, kw) = iid_decode(qw, iidrep)
            if iid > 0:
                return query_auth_read(iid)
    return (None, "Not a valid id {}".format(iidrep))


def query_auth_read(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user is not None
    else:
        q_records = db.executesql(
            """
select * from query where id = {}
;
""".format(
                iid
            ),
            as_dict=True,
        )
        q_record = q_records[0] if q_records else {}
        if q_record:
            authorized = q_record["is_shared"] or (
                auth.user is not None and q_record["created_by"] == auth.user.id
            )
    msg = (
        "No query with id {}".format(iid)
        if authorized is None
        else "You have no access to item with id {}".format(iid)
    )
    return (authorized, msg)


def word_auth_read(vr, iid):
    authorized = None
    if not iid or vr not in passage_dbs:
        authorized = False
    else:
        words = passage_dbs[vr].executesql(
            """
select * from lexicon where id = '{}'
;
""".format(
                iid
            ),
            as_dict=True,
        )
        word = words[0] if words else {}
        if word:
            authorized = True
    msg = (
        "No word with id {}".format(iid)
        if authorized is None
        else "No data version {}".format(vr)
        if vr not in passage_dbs
        else ""
    )
    return (authorized, msg)


def query_auth_write(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user is not None
    else:
        q_records = db.executesql(
            """
select * from query where id = {}
;
""".format(
                iid
            ),
            as_dict=True,
        )
        q_record = q_records[0] if q_records else {}
        if q_record is not None:
            authorized = (
                auth.user is not None and q_record["created_by"] == auth.user.id
            )
    msg = (
        "No item with id {}".format(iid)
        if authorized is None
        else "You have no access to create/modify item with id {}".format(iid)
    )
    return (authorized, msg)


@auth.requires_login()
def auth_write(label):
    authorized = auth.user is not None
    msg = "You have no access to create/modify a {}".format(label)
    return (authorized, msg)


def auth_read(label):
    authorized = True
    msg = "You have no access to create/modify a {}".format(label)
    return (authorized, msg)


def get_qx(vr, iid):
    recordx = db.executesql(
        """
select id from query_exe where query_id = {} and version = '{}'
;
""".format(
            iid, vr
        )
    )
    if recordx is None or len(recordx) != 1:
        return None
    return recordx[0][0]


def count_monads(rows):
    covered = set()
    for (b, e) in rows:
        covered |= set(range(b, e + 1))
    return len(covered)


def store_monad_sets(vr, iid, rows):
    xid = get_qx(vr, iid)
    if xid is None:
        return
    db.executesql(
        """
delete from monads where query_exe_id={}
;
""".format(
            xid
        )
    )
    # Here we clear stuff that will become invalid because of a (re)execution of a query
    # and the deleting of previous results and the storing of new results.
    clear_cache(cache, r"^verses_{}_q_{}_".format(vr, iid))
    clear_cache(cache, r"^items_q_{}_".format(vr))
    clear_cache(cache, r"^chart_{}_q_{}_".format(vr, iid))
    nrows = len(rows)
    if nrows == 0:
        return

    limit_row = 10000
    start = """
insert into monads (query_exe_id, first_m, last_m) values
"""
    query = ""
    r = 0
    while r < nrows:
        if query != "":
            db.executesql(query)
            query = ""
        query += start
        s = min(r + limit_row, len(rows))
        row = rows[r]
        query += "({},{},{})".format(xid, row[0], row[1])
        if r + 1 < nrows:
            for row in rows[r + 1:s]:
                query += ",({},{},{})".format(xid, row[0], row[1])
        r = s
    if query != "":
        db.executesql(query)
        query = ""


def load_q_hits(vr, iid):
    xid = get_qx(vr, iid)
    if xid is None:
        return normalize_ranges([])
    monad_sets = db.executesql(
        """
select first_m, last_m from monads where query_exe_id = {} order by first_m
;
""".format(
            xid
        )
    )
    return normalize_ranges(monad_sets)


def load_w_occs(vr, lexeme_id):
    monads = (
        passage_dbs[vr].executesql(
            """
select anchor from word_verse where lexicon_id = '{}' order by anchor
;
""".format(
                lexeme_id
            )
        )
        if vr in passage_dbs
        else []
    )
    return collapse_into_ranges(monads)


def count_n_notes(uid, kw):
    kw_sql = kw.replace("'", "''")
    myid = auth.user.id if auth.user is not None else None
    extra = """ or created_by = {} """.format(uid) if myid == uid else ""
    sql = """
select
    version,
    count(id) as amount
from note
where keywords like '% {} %' and (is_shared = 'T' {})
group by version
;""".format(
        kw_sql, extra
    )
    records = note_db.executesql(sql)
    vrs = set()
    versions_info = {}
    for (vr, amount) in records:
        vrs.add(vr)
        versions_info[vr] = dict(n=amount)
    return versions_info


def load_n_notes(vr, iid, kw):
    clause_atom_first = from_cache(
        cache, "clause_atom_f_{}_".format(vr), lambda: get_clause_atom_fmonad(vr), None
    )
    kw_sql = kw.replace("'", "''")
    myid = auth.user.id if auth.user is not None else None
    extra = """ or created_by = {} """.format(uid) if myid == iid else ""
    sql = """
select book, clause_atom from note
where keywords like '% {} %' and version = '{}' and (is_shared = 'T' {})
;
""".format(
        kw_sql, vr, extra
    )
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
    if fromset is not None:
        covered = fromset
    else:
        for (start, end) in ranges:
            for i in range(start, end + 1):
                covered.add(i)
    cur_start = None
    cur_end = None
    result = []
    for i in sorted(covered):
        if i not in covered:
            if cur_end is not None:
                result.append((cur_start, cur_end - 1))
            cur_start = None
            cur_end = None
        elif cur_end is None or i > cur_end:
            if cur_end is not None:
                result.append((cur_start, cur_end - 1))
            cur_start = i
            cur_end = i + 1
        else:
            cur_end = i + 1
    if cur_end is not None:
        result.append((cur_start, cur_end - 1))
    return (len(covered), result)


def get_pagination(vr, p, monad_sets):
    verse_boundaries = (
        from_cache(
            cache,
            "verse_boundaries_{}_".format(vr),
            lambda: passage_dbs[vr].executesql(
                """
select first_m, last_m from verse order by id
;
"""
            ),
            None,
        )
        if vr in passage_dbs
        else []
    )
    m = 0  # monad range index, walking through monad_sets
    v = 0  # verse id, walking through verse_boundaries
    nvp = 0  # number of verses added to current page
    nvt = 0  # number of verses added in total
    lm = len(monad_sets)
    lv = len(verse_boundaries)
    cur_page = 1  # current page
    verse_ids = []
    verse_monads = set()
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
            v += 1
        else:
            if m_e < v_e:
                m += 1
            else:
                v += 1

    verses = verse_ids if p <= cur_page and len(verse_ids) else None
    return (nvt, cur_page if nvt else 0, verses, list(verse_monads))


def get_chart(
    vr, monad_sets
):  # get data for a chart of the monadset: organized by book and block
    # return a dict keyed by book, with values lists of blocks
    # (chapter num, start point, end point, number of results, size)

    monads = flatten(monad_sets)
    chart = {}
    chart_order = []
    if len(monads):
        (books, books_order, book_id, book_name) = from_cache(
            cache, "books_{}_".format(vr), lambda: get_books(passage_dbs, vr), None
        )
        (blocks, block_mapping) = from_cache(
            cache, "blocks_{}_".format(vr), lambda: get_blocks(vr), None
        )
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
