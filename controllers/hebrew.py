#!/usr/bin/env python

from gluon.custom_import import track_changes

import json

from checks import TPS

from helpers import (
    Viewsettings,
    colorpicker,
    getRequestVal,
    style,
    tp_labels,
    tab_views,
    tr_info,
    tr_labels,
    iid_decode,
    booklangs,
    booknames,
    booktrans,
    clear_cache,
    debug,
    flatten,
    count_monads,
)
from viewdefs import get_fields

from boiler import LEGEND

from check import CHECK
from caching import CACHING
from chunk import CHUNK
from material import MATERIAL
from word import WORD
from query import QUERY
from querytree import QUERYTREE
from note import NOTE
from notetree import NOTETREE
from querychapter import QUERYCHAPTER
from side import SIDE
from chart import CHART

from mql import mql
from get_db_config import emdros_versions

Check = CHECK(request)
Caching = CACHING(cache)
Chunk = CHUNK(Caching, passage_dbs, versions)
Material = MATERIAL(Caching, passage_dbs)
Word = WORD(Caching, passage_dbs, versions)
Query = QUERY(Check, Caching, auth, db, passage_dbs, versions)
QueryTree = QUERYTREE(auth, db, version_order, version_index)
Note = NOTE(Caching, Chunk, auth, db, note_db, passage_dbs, versions)
NoteTree = NOTETREE(auth, note_db, version_order, version_index)
QueryChapter = QUERYCHAPTER(Caching, db, passage_dbs)
Side = SIDE(Caching, Material, Word, Query, Note)
Chart = CHART(Chunk, Word, Query, Note)

Query.dep(QueryChapter)

track_changes(True)


def books():
    session.forget(response)
    jsinit = f"""
var bookla = {json.dumps(booknames["Hebrew"]["la"])};
var booktrans = {json.dumps(booktrans)};
var booklangs = {json.dumps(booklangs["Hebrew"])};
"""
    return dict(jsinit=jsinit)


def text():
    session.forget(response)

    for vr in versions:
        QueryChapter.makeQCindex(vr)

    return dict(
        viewsettings=Viewsettings(Chunk, URL, versions),
        colorpicker=colorpicker,
        legend=LEGEND,
        tp_labels=tp_labels,
        tab_views=tab_views,
        tr_labels=tr_labels,
        tr_info=tr_info,
    )


def material():
    session.forget(response)
    mr = getRequestVal("material", "", "mr")
    qw = getRequestVal("material", "", "qw")
    vr = getRequestVal("material", "", "version")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    tp = getRequestVal("material", "", "tp")
    tr = getRequestVal("material", "", "tr")
    lang = getRequestVal("material", "", "lang")
    iidrep = getRequestVal("material", "", "iid")
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
    page = getRequestVal("material", "", "page")
    return Material.get(vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang)


def verse():
    session.forget(response)
    msgs = []
    vr = getRequestVal("material", "", "version")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    vs = getRequestVal("material", "", "verse")
    tr = getRequestVal("material", "", "tr")

    if request.extension == "json":
        return (Chunk.get_verse_simple(vr, bk, ch, vs),)

    if vs is None:
        return dict(good=False, msgs=msgs)
    return (Chunk.get_verse(vr, bk, ch, vs, tr, msgs),)


def cnotes():
    session.forget(response)
    myid = None
    msgs = []
    if auth.user:
        myid = auth.user.id
    logged_in = myid is not None
    vr = getRequestVal("material", "", "version")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    vs = getRequestVal("material", "", "verse")
    edit = Check.isBool("edit")
    save = Check.isBool("save")
    clause_atoms = Chunk.get_clause_atoms(vr, bk, ch, vs)
    changed = False
    now = request.utcnow

    if save:
        if myid is None:
            msgs.append(("error", "You have to be logged in when you save notes"))
        else:
            notes = (
                json.loads(request.post_vars.notes)
                if request.post_vars and request.post_vars.notes
                else []
            )
            changed = Note.save(myid, vr, bk, ch, vs, now, notes, clause_atoms, msgs)
    return Note.inChapter(
        vr, bk, ch, vs, myid, clause_atoms, changed, now, msgs, logged_in, edit
    )


def sidem():
    session.forget(response)
    vr = getRequestVal("material", "", "version")
    qw = getRequestVal("material", "", "qw")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    pub = getRequestVal("highlights", qw, "pub") if qw != "w" else ""
    debug(f"cached function PUB={pub}")
    return Side.get(vr, qw, bk, ch, pub)


def query():
    session.forget(response)
    iidrep = getRequestVal("material", "", "iid")
    request.vars["mr"] = "r"
    request.vars["qw"] = "q"
    if request.extension == "json":
        (authorized, msg) = item_access_read(iidrep=iidrep)
        if not authorized:
            result = dict(good=False, msg=[msg], data={})
        else:
            vr = getRequestVal("material", "", "version")
            msgs = []
            (iid, kw) = iid_decode("q", iidrep)
            qrecord = Query.get_info(
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
                f'''"{x.replace('"', '""')}"''' if '"' in x or "," in x else x
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
    vr = getRequestVal("material", "", "version")
    iidrep = getRequestVal("material", "", "iid")
    qw = getRequestVal("material", "", "qw")
    tp = getRequestVal("material", "", "tp")
    extra = getRequestVal("rest", "", "extra")
    if extra:
        extra = "_" + extra
    if len(extra) > 64:
        extra = extra[0:64]
    (iid, kw) = iid_decode(qw, iidrep)
    iidrep2 = iid_decode(qw, iidrep, rsep=" ")
    filename = f"{vr}_{style[qw]['t']}{iidrep2}_{tp_labels[tp]}{extra}.csv"
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        return dict(filename=filename, data=msg)
    hfields = get_fields(tp, qw=qw)
    if qw == "n":
        head_row = ["book", "chapter", "verse"] + [hf[1] for hf in hfields]
        kw_sql = kw.replace("'", "''")
        myid = auth.user.id if auth.user is not None else None
        extra = "" if myid is None else f""" or created_by = {myid} """

        hflist = ", ".join(hf[0] for hf in hfields)
        sql = f"""
select
    shebanq_note.note.book, shebanq_note.note.chapter, shebanq_note.note.verse,
    {hflist}
from shebanq_note.note
inner join book on shebanq_note.note.book = book.name
inner join clause_atom on clause_atom.ca_num = shebanq_note.note.clause_atom
    and clause_atom.book_id = book.id
where shebanq_note.note.keywords like '% {kw_sql} %'
    and shebanq_note.note.version = '{vr}'
    and (shebanq_note.note.is_shared = 'T' {extra})
;
"""
        data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
    else:
        head_row = ["book", "chapter", "verse"] + [hf[1] for hf in hfields]
        (nmonads, monad_sets) = Query.load(vr, iid) if qw == "q" else Word.load(vr, iid)
        monads = flatten(monad_sets)
        data = []
        if len(monads):
            hflist = ", ".join(f"word.{hf[0]}" for hf in hfields)
            monadsVal = ",".join(str(x) for x in monads)
            sql = f"""
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
    word.word_number in ({monadsVal})
order by
    word.word_number
;
"""
            data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
    return dict(filename=filename, data=csv([head_row] + list(data)))


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    vr = getRequestVal("material", "", "version")
    iidrep = getRequestVal("material", "", "iid")
    qw = getRequestVal("material", "", "qw")
    (authorized, msg) = item_access_read(iidrep=iidrep)
    if not authorized:
        result = Chart.compose(vr, [])
        result.update(qw=qw)
        return result
    return Chart.get(vr, qw, iidrep)


def sideqm():
    session.forget(response)
    iidrep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
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
    iidrep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
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
    iidrep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
    msg = f"Not a valid id {iidrep}"
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
    iidrep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
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
    q_record = Query.get_info(
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
    vr = getRequestVal("material", "", "version")
    iidrep = getRequestVal("material", "", "iid")
    (iid, kw) = iid_decode("w", iidrep)
    (authorized, msg) = word_auth_read(vr, iid)
    if not authorized:
        msgs.append(("error", msg))
        return dict(
            wr=dict(),
            w=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    w_record = Word.get_info(iid, vr, msgs)
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
    vr = getRequestVal("material", "", "version")
    iidrep = getRequestVal("material", "", "iid")
    (iid, kw) = iid_decode("n", iidrep)
    if not iid:
        msg = f"Not a valid id {iid}"
        msgs.append(("error", msg))
        return dict(
            nr=dict(),
            n=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    n_record = Note.get_info(iidrep, vr, msgs)
    return dict(
        vr=vr,
        nr=n_record,
        n=json.dumps(n_record),
        msgs=json.dumps(msgs),
    )


def words():
    session.forget(response)
    viewsettings = Viewsettings(Chunk, URL, versions)
    vr = getRequestVal("material", "", "version", default=False)
    if not vr:
        vr = viewsettings.theversion()
    lan = getRequestVal("rest", "", "lan")
    letter = getRequestVal("rest", "", "letter")
    return Word.page(viewsettings, vr, lan=lan, letter=letter)


def queries():
    session.forget(response)
    msgs = []
    qid = Check.isId("goto", "q", "query", msgs)
    if qid is not None:
        if not query_auth_read(qid):
            qid = 0
    return dict(
        viewsettings=Viewsettings(Chunk, URL, versions),
        qid=qid,
    )


def notes():
    session.forget(response)
    msgs = []
    nkid = Check.isId("goto", "n", "note", msgs)
    (may_upload, myid) = check_upload()
    return dict(
        viewsettings=Viewsettings(Chunk, URL, versions),
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
        sql = f"""
select uid from uploaders where uid = {myid}
    """
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
        good = Note.upload(myid, request.vars.file, request.utcnow, msgs)
    else:
        good = False
        msgs.append(["error", "you are not allowed to upload notes as csv files"])
    return dict(data=json.dumps(dict(msgs=msgs, good=good)))


# the query was:
#
#  select id, entry_heb, entryid_heb, lan, gloss from lexicon order by lan, entryid_heb
#
# normal sorting is not good enough: the pointed shin and sin turn out after the tav
# I will sort with key entryid_heb where every pointed shin/sin
# is preceded by an unpointed one.
# The unpointed one does turn up in the right place.


def queriesr():
    session.forget(response)
    return Query.recent()


def query_tree():
    session.forget(response)
    return QueryTree.get(request.utcnow)


def note_tree():
    session.forget(response)
    return NoteTree.get(request.utcnow)


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
        if tp not in TPS:
            msgs.append(("error", f"unknown type {tp}!"))
            break
        (label, table) = TPS[tp]
        lid = Check.isId("lid", tp, label, msgs)
        upd = request.vars.upd
        if lid is None:
            break
        if upd not in {"true", "false"}:
            msgs.append(("error", f"invalid instruction {upd}!"))
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
                            f"invalid instruction for organization {do_new_o}!",
                        )
                    )
                    break
                do_new_o = do_new_o == "true"
                if do_new_p not in {"true", "false"}:
                    msgs.append(
                        (
                            "error",
                            f"invalid instruction for project {do_new_p}!",
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
                    oid = Check.isId("oid", "o", TPS["o"][0], msgs)
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
                    pid = Check.isId("pid", "p", TPS["o"][0], msgs)
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
                    f"""
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
where query.id = {lid}
;
""",
                    as_dict=True,
                )
        else:
            if lid == 0:
                dbrecord = [0, "", ""]
            else:
                dbrecord = db.executesql(
                    f"""
select {",".join(fields)} from {table} where id = {lid}
;
""",
                    as_dict=True,
                )
        if not dbrecord:
            msgs.append(("error", f"No {label} with id {lid}"))
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
    (label, table) = TPS[tp]
    use_values = {}
    for i in range(len(fields)):
        field = fields[i]
        value = fvalues[i] if fvalues is not None else request.vars[field]
        use_values[field] = value

    for x in [1]:
        valsql = Check.isName(
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
            val = Check.isId(
                "oid", "o", TPS["o"][0], msgs, valrep=str(use_values["organization"])
            )
            if val is None:
                break
            valsql = Check.isRel("o", val, msgs)
            if valsql is None:
                break
            updrecord["organization"] = valsql
            val = Check.isId(
                "pid", "p", TPS["p"][0], msgs, valrep=str(use_values["project"])
            )
            valsql = Check.isRel("p", val, msgs)
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
            valsql = Check.isWebsite(tp, use_values["website"], msgs)
            if valsql is None:
                break
            updrecord["website"] = valsql
        good = True
    if good:
        if lid:
            fieldvals = [f" {f} = '{updrecord[f]}'" for f in fields]
            sql = f"""update {table} set{",".join(fieldvals)} where id = {lid};"""
            thismsg = "updated"
        else:
            fieldvals = [f"'{updrecord[f]}'" for f in fields]
            sql = f"""
insert into {table} ({",".join(fields)}) values ({",".join(fieldvals)})
;
"""
            thismsg = f"{label} added"
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
        qid = Check.isId("qid", "q", "query", msgs)
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
        now = request.utcnow
        (good, mod_dates, mod_cls, extra) = Query.upd_field(
            vr, qid, fname, val, now, msgs
        )
    return dict(
        data=json.dumps(
            dict(
                msgs=msgs, good=good, mod_dates=mod_dates, mod_cls=mod_cls, extra=extra
            )
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

    is_published = False
    is_shared = False

    for x in [1]:
        qid = Check.isId("qid", "q", "query", msgs)
        if qid is None:
            break
        (authorized, msg) = query_auth_write(qid)
        if not authorized:
            msgs.append(("error", msg))
            break

        Query.verify_version(qid, vr)
        oldrecord = db.executesql(
            f"""
select
    query.name as name,
    query.description as description,
    query.is_shared as is_shared,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{vr}'
where query.id = {qid}
;
""",
            as_dict=True,
        )
        if oldrecord is None or len(oldrecord) == 0:
            msgs.append(("error", f"No query with id {qid}"))
            break
        oldvals = oldrecord[0]
        is_shared = oldvals["is_shared"] == "T"
        is_published = oldvals["is_published"] == "T"
        if not is_published:
            # newname = str(request.vars.name, encoding="utf-8")
            newname = request.vars.name
            if oldvals["name"] != newname:
                valsql = Check.isName("q", qid, myid, newname, msgs)
                if valsql is None:
                    break
                flds["name"] = valsql
                flds["modified_on"] = request.utcnow
            newmql = request.vars.mql
            # newmql_u = str(newmql, encoding="utf-8")
            newmql_u = newmql
            if oldvals["mql"] != newmql_u:
                msgs.append(("warning", "query body modified"))
                valsql = Check.isMql("q", newmql_u, msgs)
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
            valsql = Check.isDescription("q", newdesc, msgs)
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
                Query.store(vr, qid, xmonads, is_shared)
                fldx["executed_on"] = request.utcnow
                fldx["eversion"] = eversion
                nresultmonads = count_monads(xmonads)
                fldx["results"] = nresults
                fldx["resultmonads"] = nresultmonads
                msgs.append(("good", "Query executed"))
            else:
                Query.store(vr, qid, [], is_shared)
            msgs.extend(this_msgs)
        if len(flds):
            fieldrep = ", ".join(f" {f} = '{flds[f]}'" for f in flds if f != "status")
            sql = f"""
update query set{fieldrep} where id = {qid}
;
"""
            db.executesql(sql)
            clear_cache(cache, r"^items_q_")
        if len(fldx):
            fieldrep = ", ".join(f" {f} = '{fldx[f]}'" for f in fldx if f != "status")
            sql = f"""
update query_exe set{fieldrep} where query_id = {qid} and version = '{vr}'
;
"""
            db.executesql(sql)
            clear_cache(cache, f"^items_q_{vr}_")
        q_record = Query.get_info(
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


def item_access_read(iidrep=getRequestVal("material", "", "iid")):
    mr = getRequestVal("material", "", "mr")
    qw = getRequestVal("material", "", "qw")
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
    return (None, f"Not a valid id {iidrep}")


def query_auth_read(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user is not None
    else:
        q_records = db.executesql(
            f"""
select * from query where id = {iid}
;
""",
            as_dict=True,
        )
        q_record = q_records[0] if q_records else {}
        if q_record:
            authorized = q_record["is_shared"] or (
                auth.user is not None and q_record["created_by"] == auth.user.id
            )
    msg = (
        f"No query with id {iid}"
        if authorized is None
        else f"You have no access to item with id {iid}"
    )
    return (authorized, msg)


def word_auth_read(vr, iid):
    authorized = None
    if not iid or vr not in passage_dbs:
        authorized = False
    else:
        words = passage_dbs[vr].executesql(
            f"""
select * from lexicon where id = '{iid}'
;
""",
            as_dict=True,
        )
        word = words[0] if words else {}
        if word:
            authorized = True
    msg = (
        f"No word with id {iid}"
        if authorized is None
        else f"No data version {vr}"
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
            f"""
select * from query where id = {iid}
;
""",
            as_dict=True,
        )
        q_record = q_records[0] if q_records else {}
        if q_record is not None:
            authorized = (
                auth.user is not None and q_record["created_by"] == auth.user.id
            )
    msg = (
        f"No item with id {iid}"
        if authorized is None
        else f"You have no access to create/modify item with id {iid}"
    )
    return (authorized, msg)


@auth.requires_login()
def auth_write(label):
    authorized = auth.user is not None
    msg = f"You have no access to create/modify a {label}"
    return (authorized, msg)


def auth_read(label):
    authorized = True
    msg = f"You have no access to create/modify a {label}"
    return (authorized, msg)
