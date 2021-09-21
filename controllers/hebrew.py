#!/usr/bin/env python

from gluon.custom_import import track_changes

import json

from constants import TPS

from blang import BOOK_LANGS, BOOK_TRANS, BOOK_NAMES
from helpers import (
    getRequestVal,
    iDecode,
    debug,
    countSlots,
)
from viewdefs import (
    colorPicker,
    getFields,
    TP_LABELS,
    TR_INFO,
    TR_LABELS,
    TAB_VIEWS,
    SHB_STYLE,
)

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
from csvdata import CSVDATA
from viewsettings import VIEWSETTINGS

from mql import mql
from dbconfig import EMDROS_VERSIONS

Check = CHECK(request)
Caching = CACHING(cache)
Chunk = CHUNK(Caching, PASSAGE_DBS)
Material = MATERIAL(Caching, PASSAGE_DBS)
Word = WORD(Caching, PASSAGE_DBS, VERSIONS)
Query = QUERY(Check, Caching, auth, db, PASSAGE_DBS, VERSIONS)
QueryTree = QUERYTREE(auth, db, VERSION_ORDER, VERSION_INDEX)
Note = NOTE(Caching, Chunk, auth, db, NOTE_DB, VERSIONS)
NoteTree = NOTETREE(auth, NOTE_DB, VERSION_ORDER, VERSION_INDEX)
QueryChapter = QUERYCHAPTER(Caching, db, PASSAGE_DBS)
Side = SIDE(Caching, Material, Word, Query, Note)
Chart = CHART(Chunk, Word, Query, Note)
CsvData = CSVDATA(auth, Word, Query, PASSAGE_DBS)

Query.dep(QueryChapter)

track_changes(True)


def books():
    session.forget(response)
    jsinit = f"""
var bookLatin = {json.dumps(BOOK_NAMES["Hebrew"]["la"])};
var bookTrans = {json.dumps(BOOK_TRANS)};
var bookLangs = {json.dumps(BOOK_LANGS["Hebrew"])};
"""
    return dict(jsinit=jsinit)


def text():
    session.forget(response)

    for vr in VERSIONS:
        QueryChapter.makeQCindex(vr)

    return dict(
        ViewSettings=VIEWSETTINGS(Chunk, URL, VERSIONS),
        colorPicker=colorPicker,
        legend=LEGEND,
        TP_LABELS=TP_LABELS,
        TAB_VIEWS=TAB_VIEWS,
        TR_LABELS=TR_LABELS,
        TR_INFO=TR_INFO,
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
    iidRep = getRequestVal("material", "", "iid")
    (authorized, msg) = authReadItem(iidRep=iidRep)
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
            slots=json.dumps([]),
        )
    page = getRequestVal("material", "", "page")
    return Material.get(vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang)


def verse():
    session.forget(response)
    msgs = []
    vr = getRequestVal("material", "", "version")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    vs = getRequestVal("material", "", "verse")
    tr = getRequestVal("material", "", "tr")

    if request.extension == "json":
        return (Chunk.getVerseSimple(vr, bk, ch, vs),)

    if vs is None:
        return dict(good=False, msgs=msgs)
    return (Chunk.getVerse(vr, bk, ch, vs, tr, msgs),)


def versenotes():
    session.forget(response)
    myId = None
    msgs = []
    if auth.user:
        myId = auth.user.id
    loggedIn = myId is not None
    vr = getRequestVal("material", "", "version")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    vs = getRequestVal("material", "", "verse")
    edit = Check.isBool("edit")
    save = Check.isBool("save")
    clauseAtoms = Chunk.getClauseAtoms(vr, bk, ch, vs)
    changed = False
    now = request.utcnow

    if save:
        if myId is None:
            msgs.append(("error", "You have to be logged in when you save notes"))
        else:
            notes = (
                json.loads(request.post_vars.notes)
                if request.post_vars and request.post_vars.notes
                else []
            )
            changed = Note.save(myId, vr, bk, ch, vs, now, notes, clauseAtoms, msgs)
    return Note.inVerse(
        vr, bk, ch, vs, myId, clauseAtoms, changed, now, msgs, loggedIn, edit
    )


def sidem():
    session.forget(response)
    vr = getRequestVal("material", "", "version")
    qw = getRequestVal("material", "", "qw")
    bk = getRequestVal("material", "", "book")
    ch = getRequestVal("material", "", "chapter")
    is_published = getRequestVal("highlights", qw, "pub") if qw != "w" else ""
    debug(f"cached function PUB={is_published}")
    return Side.get(vr, qw, bk, ch, is_published)


def word():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "w"
    request.vars["page"] = 1
    return text()


def query():
    session.forget(response)
    iidRep = getRequestVal("material", "", "iid")
    request.vars["mr"] = "r"
    request.vars["qw"] = "q"
    if request.extension == "json":
        (authorized, msg) = authReadItem(iidRep=iidRep)
        if not authorized:
            result = dict(good=False, msg=[msg], data={})
        else:
            vr = getRequestVal("material", "", "version")
            msgs = []
            (iid, keywords) = iDecode("q", iidRep)
            qrecord = Query.getInfo(
                False, iid, vr, msgs, withIds=False, singleVersion=False, po=True
            )
            result = dict(good=qrecord is not None, msg=msgs, data=qrecord)
        return dict(data=json.dumps(result))
    else:
        request.vars["page"] = 1
    return text()


def note():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "n"
    request.vars["page"] = 1
    return text()


def item():
    """controller to produce a csv file of query results or lexeme occurrences
    Where fields are specified in the current legend
    """
    session.forget(response)
    vr = getRequestVal("material", "", "version")
    iidRep = getRequestVal("material", "", "iid")
    qw = getRequestVal("material", "", "qw")
    tp = getRequestVal("material", "", "tp")
    extra = getRequestVal("rest", "", "extra")
    if extra:
        extra = "_" + extra
    if len(extra) > 64:
        extra = extra[0:64]
    (iid, keywords) = iDecode(qw, iidRep)
    iidRep2 = iDecode(qw, iidRep, rsep=" ")
    fileName = f"{vr}_{SHB_STYLE[qw]['t']}{iidRep2}_{TP_LABELS[tp]}{extra}.csv"
    (authorized, msg) = authReadItem(iidRep=iidRep)

    if not authorized:
        return dict(fileName=fileName, data=msg)

    hebrewFields = getFields(tp, qw=qw)
    data = CsvData(vr, iid, keywords, hebrewFields)
    return dict(fileName=fileName, data=data)


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    vr = getRequestVal("material", "", "version")
    iidRep = getRequestVal("material", "", "iid")
    qw = getRequestVal("material", "", "qw")
    (authorized, msg) = authReadItem(iidRep=iidRep)
    if not authorized:
        result = Chart.compose(vr, [])
        result.update(qw=qw)
        return result
    return Chart.get(vr, qw, iidRep)


def sidewm():
    session.forget(response)
    iidRep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
    (authorized, msg) = authReadItem(iidRep=iidRep)
    if authorized:
        msg = "fetching word"
    return dict(
        load=LOAD(
            "hebrew",
            "sidew",
            extension="load",
            vars=dict(mr="r", qw="w", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="wordbody",
            content=msg,
        )
    )


def sideqm():
    session.forget(response)
    iidRep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
    (authorized, msg) = authReadItem(iidRep=iidRep)
    if authorized:
        msg = "fetching query"
    return dict(
        load=LOAD(
            "hebrew",
            "sideq",
            extension="load",
            vars=dict(mr="r", qw="q", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="querybody",
            content=msg,
        )
    )


def sidenm():
    session.forget(response)
    iidRep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
    msg = f"Not a valid id {iidRep}"
    if iidRep:
        msg = "fetching note set"
    return dict(
        load=LOAD(
            "hebrew",
            "siden",
            extension="load",
            vars=dict(mr="r", qw="n", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="notebody",
            content=msg,
        )
    )


def sidew():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "word", extension="", vars=request.vars))
    msgs = []
    vr = getRequestVal("material", "", "version")
    iidRep = getRequestVal("material", "", "iid")
    (iid, keywords) = iDecode("w", iidRep)
    (authorized, msg) = authReadWord(vr, iid)
    if not authorized:
        msgs.append(("error", msg))
        return dict(
            wr=dict(),
            w=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    wordRecord = Word.getInfo(iid, vr, msgs)
    return dict(
        vr=vr,
        wr=wordRecord,
        w=json.dumps(wordRecord),
        msgs=json.dumps(msgs),
    )


def sideq():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "query", extension="", vars=request.vars))
    msgs = []
    iidRep = getRequestVal("material", "", "iid")
    vr = getRequestVal("material", "", "version")
    (iid, keywords) = iDecode("q", iidRep)
    (authorized, msg) = authReadQuery(iid)
    if iid == 0 or not authorized:
        msgs.append(("error", msg))
        return dict(
            writable=False,
            iidRep=iidRep,
            vr=vr,
            qr=dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
            emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
        )
    queryRecord = Query.getInfo(
        auth.user is not None,
        iid,
        vr,
        msgs,
        withIds=True,
        singleVersion=False,
        po=True,
    )
    if queryRecord is None:
        return dict(
            writable=True,
            iidRep=iidRep,
            vr=vr,
            qr=dict(),
            q=json.dumps(dict()),
            msgs=json.dumps(msgs),
            emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
        )

    (authorized, msg) = authWriteQuery(iid=iid)

    return dict(
        writable=authorized,
        iidRep=iidRep,
        vr=vr,
        qr=queryRecord,
        q=json.dumps(queryRecord),
        msgs=json.dumps(msgs),
        emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
    )


def siden():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "note", extension="", vars=request.vars))
    msgs = []
    vr = getRequestVal("material", "", "version")
    iidRep = getRequestVal("material", "", "iid")
    (iid, keywords) = iDecode("n", iidRep)
    if not iid:
        msg = f"Not a valid id {iid}"
        msgs.append(("error", msg))
        return dict(
            nr=dict(),
            n=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    noteRecord = Note.getInfo(iidRep, vr, msgs)
    return dict(
        vr=vr,
        nr=noteRecord,
        n=json.dumps(noteRecord),
        msgs=json.dumps(msgs),
    )


def words():
    session.forget(response)
    ViewSettings = VIEWSETTINGS(Chunk, URL, VERSIONS)
    vr = getRequestVal("material", "", "version", default=False)
    if not vr:
        vr = ViewSettings.theversion()
    lan = getRequestVal("rest", "", "lan")
    letter = getRequestVal("rest", "", "letter")
    return Word.page(ViewSettings, vr, lan=lan, letter=letter)


def queries():
    session.forget(response)
    msgs = []
    query_id = Check.isId("goto", "q", "query", msgs)
    if query_id is not None:
        if not authReadQuery(query_id):
            query_id = 0
    return dict(
        ViewSettings=VIEWSETTINGS(Chunk, URL, VERSIONS),
        query_id=query_id,
    )


def notes():
    session.forget(response)
    msgs = []
    key_id = Check.isId("goto", "n", "note", msgs)
    (mayUpload, myId) = authUpload()
    return dict(
        ViewSettings=VIEWSETTINGS(Chunk, URL, VERSIONS),
        key_id=key_id,
        mayUpload=mayUpload,
        user_id=myId,
    )


def authUpload(no_controller=True):
    myId = None
    mayUpload = False
    if auth.user:
        myId = auth.user.id
    if myId:
        sql = f"""
select uid from uploaders where uid = {myId}
    """
        records = db.executesql(sql)
        mayUpload = records is not None and len(records) == 1 and records[0][0] == myId
    return (mayUpload, myId)


@auth.requires_login()
def noteupload():
    session.forget(response)
    msgs = []
    good = True
    user_id = request.vars.user_id
    (mayUpload, myId) = authUpload()
    if mayUpload and str(myId) == user_id:
        good = Note.upload(myId, request.vars.file, request.utcnow, msgs)
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


def notetree():
    session.forget(response)
    return NoteTree.get(request.utcnow)


def queriesr():
    session.forget(response)
    return Query.recent()


def querytree():
    session.forget(response)
    return QueryTree.get(request.utcnow)


def querymeta():
    session.forget(response)
    msgs = []
    record = {}
    orgRecord = {}
    projectRecord = {}
    good = False
    orgGood = False
    projectGood = False
    myId = auth.user.id if auth.user is not None else None
    for x in [1]:
        tp = request.vars.tp
        if tp not in TPS:
            msgs.append(("error", f"unknown type {tp}!"))
            break
        (label, table) = TPS[tp]
        obj_id = Check.isId("obj_id", tp, label, msgs)
        upd = request.vars.upd
        if obj_id is None:
            break
        if upd not in {"true", "false"}:
            msgs.append(("error", f"invalid instruction {upd}!"))
            break
        upd = True if upd == "true" else False
        if upd and not myId:
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
                authWriteQuery(obj_id) if tp == "q" else authWrite(label)
            )
        else:
            (authorized, msg) = authReadQuery(obj_id) if tp == "q" else authRead(label)
        if not authorized:
            msgs.append(("error", msg))
            break
        if upd:
            fieldValues = None
            if tp == "q":
                subfields = ["name", "website"]
                fieldValues = [request.vars.name]
                doNewOrg = request.vars.do_new_o
                doNewProject = request.vars.doNewProject
                if doNewOrg not in {"true", "false"}:
                    msgs.append(
                        (
                            "error",
                            f"invalid instruction for organization {doNewOrg}!",
                        )
                    )
                    break
                doNewOrg = doNewOrg == "true"
                if doNewProject not in {"true", "false"}:
                    msgs.append(
                        (
                            "error",
                            f"invalid instruction for project {doNewProject}!",
                        )
                    )
                    break
                doNewProject = doNewProject == "true"
                orgGood = True
                if doNewOrg:
                    (orgGood, org_id) = updQueryMeta(
                        "o",
                        0,
                        myId,
                        subfields,
                        msgs,
                        fieldValues=[request.vars.org_name, request.vars.org_website],
                    )
                    if orgGood:
                        orgRecord = dict(
                            id=org_id,
                            name=request.vars.org_name,
                            website=request.vars.org_website,
                        )
                else:
                    org_id = Check.isId("org_id", "o", TPS["o"][0], msgs)
                projectGood = True
                if doNewProject:
                    (projectGood, project_id) = updQueryMeta(
                        "p",
                        0,
                        myId,
                        subfields,
                        msgs,
                        fieldValues=[
                            request.vars.project_name,
                            request.vars.project_website,
                        ],
                    )
                    if projectGood:
                        projectRecord = dict(
                            id=project_id,
                            name=request.vars.project_name,
                            website=request.vars.project_website,
                        )
                else:
                    project_id = Check.isId("project_id", "p", TPS["o"][0], msgs)
                if not orgGood or not projectGood:
                    break
                if org_id is None or project_id is None:
                    break
                fieldValues.extend([org_id, project_id])
            (good, obj_idNew) = updQueryMeta(
                tp, obj_id, myId, fields, msgs, fieldValues=fieldValues
            )
            if not good:
                break
            obj_id = obj_idNew
        else:
            good = True
        dbRecord = None
        if tp == "q":
            if obj_id == 0:
                dbRecord = [0, "", 0, "", "", 0, "", ""]
            else:
                dbRecord = db.executesql(
                    f"""
select
query.id as id,
query.name as name,
organization.id as org_id,
organization.name as org_name,
organization.website as org_website,
project.id as project_id,
project.name as project_name,
project.website as project_website
from query
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
where query.id = {obj_id}
;
""",
                    asDict=True,
                )
        else:
            if obj_id == 0:
                dbRecord = [0, "", ""]
            else:
                dbRecord = db.executesql(
                    f"""
select {",".join(fields)} from {table} where id = {obj_id}
;
""",
                    asDict=True,
                )
        if not dbRecord:
            msgs.append(("error", f"No {label} with id {obj_id}"))
            break
        record = dbRecord[0]
    return dict(
        data=json.dumps(
            dict(
                record=record,
                orgRecord=orgRecord,
                projectRecord=projectRecord,
                msgs=msgs,
                good=good,
                orgGood=orgGood,
                projectGood=projectGood,
            )
        )
    )


def updQueryMeta(tp, obj_id, myId, fields, msgs, fieldValues=None):
    updMeta = {}
    good = False
    (label, table) = TPS[tp]
    useValues = {}
    for i in range(len(fields)):
        field = fields[i]
        value = fieldValues[i] if fieldValues is not None else request.vars[field]
        useValues[field] = value

    for x in [1]:
        valSql = Check.isName(
            tp,
            obj_id,
            myId,
            useValues["name"],
            msgs,
        )
        if valSql is None:
            break
        updMeta["name"] = valSql
        if tp == "q":
            val = Check.isId(
                "org_id", "o", TPS["o"][0], msgs, valrep=str(useValues["organization"])
            )
            if val is None:
                break
            valSql = Check.isRel("o", val, msgs)
            if valSql is None:
                break
            updMeta["organization"] = valSql
            val = Check.isId(
                "project_id", "p", TPS["p"][0], msgs, valrep=str(useValues["project"])
            )
            valSql = Check.isRel("p", val, msgs)
            if valSql is None:
                break
            updMeta["project"] = valSql
            fld = "modified_on"
            updMeta[fld] = request.utcnow
            fields.append(fld)
            if obj_id == 0:
                fld = "created_on"
                updMeta[fld] = request.utcnow
                fields.append(fld)
                fld = "created_by"
                updMeta[fld] = myId
                fields.append(fld)
        else:
            valSql = Check.isWebsite(tp, useValues["website"], msgs)
            if valSql is None:
                break
            updMeta["website"] = valSql
        good = True
    if good:
        if obj_id:
            fieldVals = [f" {f} = '{updMeta[f]}'" for f in fields]
            sql = f"""update {table} set{",".join(fieldVals)} where id = {obj_id};"""
            thisMsg = "updated"
        else:
            fieldVals = [f"'{updMeta[f]}'" for f in fields]
            sql = f"""
insert into {table} ({",".join(fields)}) values ({",".join(fieldVals)})
;
"""
            thisMsg = f"{label} added"
        db.executesql(sql)
        if obj_id == 0:
            obj_id = db.executesql(
                """
select last_insert_id() as x
;
"""
            )[0][0]

        msgs.append(("good", thisMsg))
    return (good, obj_id)


def querymetafield():
    session.forget(response)
    msgs = []
    good = False
    modDates = {}
    modCls = ""
    extra = {}
    for x in [1]:
        query_id = Check.isId("query_id", "q", "query", msgs)
        if query_id is None:
            break
        fname = request.vars.fname
        val = request.vars.val
        vr = request.vars.version
        if fname is None or fname not in {"is_shared", "is_published"}:
            msgs.append("error", "Illegal field name {}")
            break
        (authorized, msg) = authWriteQuery(query_id)
        if not authorized:
            msgs.append(("error", msg))
            break
        now = request.utcnow
        (good, modDates, modCls, extra) = Query.updField(
            vr, query_id, fname, val, now, msgs
        )
    return dict(
        data=json.dumps(
            dict(msgs=msgs, good=good, modDates=modDates, modCls=modCls, extra=extra)
        )
    )


def querymetafields():
    session.forget(response)
    msgs = []
    good = False
    myId = auth.user.id if auth.user is not None else None
    flds = {}
    fldx = {}
    vr = request.vars.version
    queryRecord = {}

    is_published = False
    is_shared = False

    for x in [1]:
        query_id = Check.isId("query_id", "q", "query", msgs)
        if query_id is None:
            break
        (authorized, msg) = authWriteQuery(query_id)
        if not authorized:
            msgs.append(("error", msg))
            break

        Query.verifyVersion(query_id, vr)
        recordOld = db.executesql(
            f"""
select
    query.name as name,
    query.description as description,
    query.is_shared as is_shared,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{vr}'
where query.id = {query_id}
;
""",
            asDict=True,
        )
        if recordOld is None or len(recordOld) == 0:
            msgs.append(("error", f"No query with id {query_id}"))
            break
        valsOld = recordOld[0]
        is_shared = valsOld["is_shared"] == "T"
        is_published = valsOld["is_published"] == "T"
        if not is_published:
            nameNew = request.vars.name
            if valsOld["name"] != nameNew:
                valSql = Check.isName("q", query_id, myId, nameNew, msgs)
                if valSql is None:
                    break
                flds["name"] = valSql
                flds["modified_on"] = request.utcnow
            mqlNew = request.vars.mql
            if valsOld["mql"] != mqlNew:
                msgs.append(("warning", "query body modified"))
                valSql = Check.isMql("q", mqlNew, msgs)
                if valSql is None:
                    break
                fldx["mql"] = valSql
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
        descriptionNew = request.vars.description
        if valsOld["description"] != descriptionNew:
            valSql = Check.isDescription("q", descriptionNew, msgs)
            if valSql is None:
                break
            flds["description"] = valSql
            flds["modified_on"] = request.utcnow
        good = True
    if good:
        execute = not is_published and request.vars.execute
        exeGood = True
        if execute == "true":
            (
                exeGood,
                limitExceeded,
                nResults,
                exeSlots,
                theseMsgs,
                emdrosVersion,
            ) = mql(vr, mqlNew)
            if exeGood and not limitExceeded:
                Query.store(vr, query_id, exeSlots, is_shared)
                fldx["executed_on"] = request.utcnow
                fldx["eversion"] = emdrosVersion
                nResultSlots = countSlots(exeSlots)
                fldx["results"] = nResults
                fldx["resultmonads"] = nResultSlots
                msgs.append(("good", "Query executed"))
            else:
                Query.store(vr, query_id, [], is_shared)
            msgs.extend(theseMsgs)
        if len(flds):
            fieldRep = ", ".join(f" {f} = '{flds[f]}'" for f in flds if f != "status")
            sql = f"""
update query set{fieldRep} where id = {query_id}
;
"""
            db.executesql(sql)
            Caching.clear(cache, r"^items_q_")
        if len(fldx):
            fieldRep = ", ".join(f" {f} = '{fldx[f]}'" for f in fldx if f != "status")
            sql = f"""
update query_exe set{fieldRep} where query_id = {query_id} and version = '{vr}'
;
"""
            db.executesql(sql)
            Caching.clear(cache, f"^items_q_{vr}_")
        queryRecord = Query.getInfo(
            auth.user is not None,
            query_id,
            vr,
            msgs,
            withIds=False,
            singleVersion=False,
            po=True,
        )

    emdrosVersionsOld = dict((x, 1) for x in EMDROS_VERSIONS[0:-1])
    return dict(
        data=json.dumps(
            dict(
                msgs=msgs,
                good=good and exeGood,
                q=queryRecord,
                emdrosVersionsOld=emdrosVersionsOld,
            )
        )
    )


def authReadItem(iidRep=getRequestVal("material", "", "iid")):
    mr = getRequestVal("material", "", "mr")
    qw = getRequestVal("material", "", "qw")
    if mr == "m":
        return (True, "")
    if qw == "w":
        return (True, "")
    if qw == "n":
        return (True, "")
    if qw == "q":
        if iidRep is not None:
            (iid, keywords) = iDecode(qw, iidRep)
            if iid > 0:
                return authReadQuery(iid)
    return (None, f"Not a valid id {iidRep}")


def authReadQuery(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user is not None
    else:
        q_records = db.executesql(
            f"""
select * from query where id = {iid}
;
""",
            asDict=True,
        )
        queryRecord = q_records[0] if q_records else {}
        if queryRecord:
            authorized = queryRecord["is_shared"] or (
                auth.user is not None and queryRecord["created_by"] == auth.user.id
            )
    msg = (
        f"No query with id {iid}"
        if authorized is None
        else f"You have no access to item with id {iid}"
    )
    return (authorized, msg)


def authReadWord(vr, iid):
    authorized = None
    if not iid or vr not in PASSAGE_DBS:
        authorized = False
    else:
        words = PASSAGE_DBS[vr].executesql(
            f"""
select * from lexicon where id = '{iid}'
;
""",
            asDict=True,
        )
        word = words[0] if words else {}
        if word:
            authorized = True
    msg = (
        f"No word with id {iid}"
        if authorized is None
        else f"No data version {vr}"
        if vr not in PASSAGE_DBS
        else ""
    )
    return (authorized, msg)


def authWriteQuery(iid):
    authorized = None
    if iid == 0:
        authorized = auth.user is not None
    else:
        q_records = db.executesql(
            f"""
select * from query where id = {iid}
;
""",
            asDict=True,
        )
        queryRecord = q_records[0] if q_records else {}
        if queryRecord is not None:
            authorized = (
                auth.user is not None and queryRecord["created_by"] == auth.user.id
            )
    msg = (
        f"No item with id {iid}"
        if authorized is None
        else f"You have no access to create/modify item with id {iid}"
    )
    return (authorized, msg)


@auth.requires_login()
def authWrite(label):
    authorized = auth.user is not None
    msg = f"You have no access to create/modify a {label}"
    return (authorized, msg)


def authRead(label):
    authorized = True
    msg = f"You have no access to create/modify a {label}"
    return (authorized, msg)
