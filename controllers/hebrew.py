#!/usr/bin/env python

from gluon.custom_import import track_changes

import json
import collections # noqa F401
# needed for views

from constants import TPS

from blang import BOOK_LANGS, BOOK_TRANS, BOOK_NAMES
from helpers import iDecode, countSlots
from viewdefs import (
    colorPicker,
    getFields,
    getVal,
    TP_LABELS,
    TR_INFO,
    TR_LABELS,
    TAB_VIEWS,
    ITEM_STYLE,
)

from boiler import LEGEND

from check import CHECK
from caching import CACHING
from pieces import Pieces
from materials import MATERIAL
from word import WORD
from query import QUERY
from querysave import QUERYSAVE
from querytree import QUERYTREE
from queryrecent import QUERYRECENT
from note import NOTE
from notesave import NOTESAVE
from notesupload import NOTESUPLOAD
from notetree import NOTETREE
from querychapter import QUERYCHAPTER
from record import RECORD
from side import SIDE
from chart import CHART
from csvdata import CSVDATA
from viewsettings import VIEWSETTINGS

from mql import mql
from dbconfig import EMDROS_VERSIONS

Check = CHECK(request, db)
Caching = CACHING(cache)
Pieces = Pieces(Caching, PASSAGE_DBS)
Word = WORD(Caching, PASSAGE_DBS, VERSIONS)
Query = QUERY(Check, Caching, auth, db, VERSIONS)
QuerySave = QUERYSAVE(Check, Caching, Query, auth, db, VERSIONS)
QueryTree = QUERYTREE(auth, db, VERSION_ORDER, VERSION_INDEX)
QueryRecent = QUERYRECENT(db)
Note = NOTE(Caching, Pieces, auth, db, NOTE_DB)
NoteSave = NOTESAVE(Caching, NOTE_DB)
NotesUpload = NOTESUPLOAD(Caching, Pieces, auth, db, NOTE_DB, VERSIONS)
NoteTree = NOTETREE(auth, NOTE_DB, VERSION_ORDER, VERSION_INDEX)
QueryChapter = QUERYCHAPTER(Caching, db, PASSAGE_DBS)
Material = MATERIAL(Caching, Word, Query, QueryChapter, Note, PASSAGE_DBS)
Record = RECORD(Check, Query, auth, db)
Side = SIDE(Caching, Material, Word, Query, Note)
Chart = CHART(Caching, Pieces, Word, Query, Note, PASSAGE_DBS)
CsvData = CSVDATA(Word, Query, auth, PASSAGE_DBS)

QuerySave.dep(QueryChapter)

track_changes(True)


def text():
    session.forget(response)

    ViewSettings = VIEWSETTINGS(Pieces, URL, VERSIONS)

    return dict(
        ViewSettings=ViewSettings,
        colorPicker=colorPicker,
        legend=LEGEND,
        TP_LABELS=TP_LABELS,
        TAB_VIEWS=TAB_VIEWS,
        TR_LABELS=TR_LABELS,
        TR_INFO=TR_INFO,
    )


def material():
    session.forget(response)
    mr = getVal("material", "", "mr")
    qw = getVal("material", "", "qw")
    vr = getVal("material", "", "version")
    bk = getVal("material", "", "book")
    ch = getVal("material", "", "chapter")
    tp = getVal("material", "", "tp")
    tr = getVal("material", "", "tr")
    lang = getVal("material", "", "lang")
    iidRep = getVal("material", "", "iid")
    (authorized, msg) = Record.authRead(mr, qw, iidRep)
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
    page = getVal("material", "", "page")
    return Material.get(vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang)


def sidematerial():
    session.forget(response)
    vr = getVal("material", "", "version")
    qw = getVal("material", "", "qw")
    bk = getVal("material", "", "book")
    ch = getVal("material", "", "chapter")
    is_published = getVal("highlights", qw, "pub") if qw != "w" else ""
    return Side.get(vr, qw, bk, ch, is_published)


def sidewordbody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "word", extension="", vars=request.vars))
    msgs = []
    vr = getVal("material", "", "version")
    iidRep = getVal("material", "", "iid")
    (iid, keywords) = iDecode("w", iidRep)
    (authorized, msg) = Word.authRead(vr, iid)
    if not authorized:
        msgs.append(("error", msg))
        return dict(
            wordRecord=dict(),
            word=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    wordRecord = Word.getInfo(iid, vr, msgs)
    return dict(
        vr=vr,
        wordRecord=wordRecord,
        word=json.dumps(wordRecord),
        msgs=json.dumps(msgs),
    )


def sidequerybody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "query", extension="", vars=request.vars))
    msgs = []
    iidRep = getVal("material", "", "iid")
    vr = getVal("material", "", "version")
    (iid, keywords) = iDecode("q", iidRep)
    (authorized, msg) = Query.authRead(iid)
    if authorized and iid == 0:
        msg = f"Not a valid query id: {iidRep}"
    if not authorized or iid == 0:
        msgs.append(("error", msg))
        return dict(
            writable=False,
            iidRep=iidRep,
            vr=vr,
            queryRecord=dict(),
            query=json.dumps(dict()),
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
            queryRecord=dict(),
            query=json.dumps(dict()),
            msgs=json.dumps(msgs),
            emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
        )

    (authorized, msg) = Query.authWrite(iid)

    return dict(
        writable=authorized,
        iidRep=iidRep,
        vr=vr,
        queryRecord=queryRecord,
        query=json.dumps(queryRecord),
        msgs=json.dumps(msgs),
        emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
    )


def sidenotebody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "note", extension="", vars=request.vars))
    msgs = []
    vr = getVal("material", "", "version")
    iidRep = getVal("material", "", "iid")
    (iid, keywords) = iDecode("n", iidRep)
    if not iid:
        msg = f"Not a valid note id: {iid}"
        msgs.append(("error", msg))
        return dict(
            noteRecord=dict(),
            note=json.dumps(dict()),
            msgs=json.dumps(msgs),
        )
    noteRecord = Note.getInfo(iidRep, vr, msgs)
    return dict(
        vr=vr,
        noteRecord=noteRecord,
        note=json.dumps(noteRecord),
        msgs=json.dumps(msgs),
    )


def sideword():
    session.forget(response)
    iidRep = getVal("material", "", "iid")
    vr = getVal("material", "", "version")
    mr = getVal("material", "", "mr")
    qw = getVal("material", "", "qw")
    (authorized, msg) = Record.authRead(mr, qw, iidRep)
    if authorized:
        msg = "fetching word"
    return dict(
        load=LOAD(
            "hebrew",
            "sidewordbody",
            extension="load",
            vars=dict(mr="r", qw="w", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="wordbody",
            content=msg,
        )
    )


def sidequery():
    session.forget(response)
    iidRep = getVal("material", "", "iid")
    vr = getVal("material", "", "version")
    mr = getVal("material", "", "mr")
    qw = getVal("material", "", "qw")
    (authorized, msg) = Record.authRead(mr, qw, iidRep)
    if authorized:
        msg = "fetching query"
    return dict(
        load=LOAD(
            "hebrew",
            "sidequerybody",
            extension="load",
            vars=dict(mr="r", qw="q", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="querybody",
            content=msg,
        )
    )


def sidenote():
    session.forget(response)
    iidRep = getVal("material", "", "iid")
    vr = getVal("material", "", "version")
    msg = f"Not a valid note id: {iidRep}"
    if iidRep:
        msg = "fetching note set"
    return dict(
        load=LOAD(
            "hebrew",
            "sidenotebody",
            extension="load",
            vars=dict(mr="r", qw="n", version=vr, iid=iidRep),
            ajax=False,
            ajax_trap=True,
            target="notebody",
            content=msg,
        )
    )


def word():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "w"
    request.vars["page"] = 1
    return text()


def query():
    session.forget(response)
    iidRep = getVal("material", "", "iid")
    mr = "r"
    qw = "q"
    request.vars["mr"] = mr
    request.vars["qw"] = qw
    if request.extension == "json":
        (authorized, msg) = Record.authRead(mr, qw, iidRep)
        if not authorized:
            result = dict(good=False, msg=[msg], data={})
        else:
            vr = getVal("material", "", "version")
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


def words():
    session.forget(response)
    ViewSettings = VIEWSETTINGS(Pieces, URL, VERSIONS)
    vr = getVal("material", "", "version", default=False)
    if not vr:
        vr = ViewSettings.theVersion()
    lan = getVal("rest", "", "lan")
    letter = getVal("rest", "", "letter")
    return Word.page(ViewSettings, vr, lan=lan, letter=letter)


def queries():
    session.forget(response)
    msgs = []
    query_id = Check.isId("goto", "q", "query", msgs)
    if query_id is not None:
        (authorized, msg) = Query.authRead(query_id)
        if not authorized:
            query_id = 0
    return dict(
        ViewSettings=VIEWSETTINGS(Pieces, URL, VERSIONS),
        query_id=query_id,
    )


def notes():
    session.forget(response)
    msgs = []
    key_id = Check.isId("goto", "n", "note", msgs)
    (authorized, myId, msg) = NotesUpload.authUpload()
    return dict(
        ViewSettings=VIEWSETTINGS(Pieces, URL, VERSIONS),
        key_id=key_id,
        mayUpload=authorized,
        user_id=myId,
    )


def queriesr():
    session.forget(response)
    return QueryRecent.recent()


def querytree():
    session.forget(response)
    return QueryTree.get(request.utcnow)


def notetree():
    session.forget(response)
    return NoteTree.get(request.utcnow)


def books():
    session.forget(response)
    jsinit = f"""
var bookLatin = {json.dumps(BOOK_NAMES["Hebrew"]["la"])};
var bookTrans = {json.dumps(BOOK_TRANS)};
var bookLangs = {json.dumps(BOOK_LANGS["Hebrew"])};
"""
    return dict(jsinit=jsinit)


def verse():
    session.forget(response)
    msgs = []
    vr = getVal("material", "", "version")
    bk = getVal("material", "", "book")
    ch = getVal("material", "", "chapter")
    vs = getVal("material", "", "verse")
    tr = getVal("material", "", "tr")

    if request.extension == "json":
        return Pieces.getVerseSimple(vr, bk, ch, vs)

    if vs is None:
        return dict(good=False, msgs=msgs)
    return Pieces.getVerse(vr, bk, ch, vs, tr, msgs)


def versenotes():
    session.forget(response)
    myId = None
    msgs = []
    if auth.user:
        myId = auth.user.id
    authenticated = myId is not None
    vr = getVal("material", "", "version")
    bk = getVal("material", "", "book")
    ch = getVal("material", "", "chapter")
    vs = getVal("material", "", "verse")
    edit = Check.isBool("edit")
    save = Check.isBool("save")
    clauseAtoms = Pieces.getClauseAtoms(vr, bk, ch, vs)
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
            changed = NoteSave.put(myId, vr, bk, ch, vs, now, notes, clauseAtoms, msgs)
    return Note.inVerse(
        vr, bk, ch, vs, myId, clauseAtoms, changed, now, msgs, authenticated, edit
    )


def item():
    """controller to produce a csv file of query results or lexeme occurrences
    Where fields are specified in the current legend
    """
    session.forget(response)
    vr = getVal("material", "", "version")
    iidRep = getVal("material", "", "iid")
    mr = getVal("material", "", "mr")
    qw = getVal("material", "", "qw")
    tp = getVal("material", "", "tp")
    extra = getVal("rest", "", "extra")
    if extra:
        extra = "_" + extra
    if len(extra) > 64:
        extra = extra[0:64]
    (iid, keywords) = iDecode(qw, iidRep)
    iidRep2 = iDecode(qw, iidRep, rsep=" ")
    fileName = f"{vr}_{ITEM_STYLE[qw]['t']}{iidRep2}_{TP_LABELS[tp]}{extra}.csv"
    (authorized, msg) = Record.authRead(mr, qw, iidRep)

    if not authorized:
        return dict(fileName=fileName, data=msg)

    hebrewFields = getFields(tp, qw=qw)
    data = CsvData.get(vr, qw, iid, keywords, hebrewFields)
    return dict(fileName=fileName, data=data)


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    vr = getVal("material", "", "version")
    iidRep = getVal("material", "", "iid")
    mr = getVal("material", "", "mr")
    qw = getVal("material", "", "qw")

    (authorized, msg) = Record.authRead(mr, qw, iidRep)
    if not authorized:
        # produce empty chart
        result = Chart.compose(vr, [])
    else:
        result = Chart.get(vr, qw, iidRep)

    result.update(qw=qw)
    result.update(msg=msg)
    return result


def noteupload():
    session.forget(response)
    msgs = []
    good = True
    (authorized, myId, msg) = NotesUpload.authUpload()
    if authorized:
        good = NotesUpload.upload(myId, request.vars.file, request.utcnow, msgs)
    else:
        good = False
        msgs.append(["error", msg])
    return dict(data=json.dumps(dict(msgs=msgs, good=good)))


def itemrecord():
    session.forget(response)
    msgs = []
    orgRecord = {}
    projectRecord = {}
    good = False
    orgGood = False
    projectGood = False
    obj_id = None
    label = None
    table = None
    fields = None

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
                Query.authWrite(obj_id) if tp == "q" else Record.authWriteGeneric(label)
            )
        else:
            (authorized, msg) = (
                Query.authRead(obj_id) if tp == "q" else Record.authReadGeneric(label)
            )
        if not authorized:
            msgs.append(("error", msg))
            break
        if upd:
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
                    (orgGood, org_id) = Record.update(
                        "o",
                        0,
                        myId,
                        subfields,
                        [request.vars.org_name, request.vars.org_website],
                        request.utcnow,
                        msgs,
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
                    (projectGood, project_id) = Record.update(
                        "p",
                        0,
                        myId,
                        subfields,
                        [request.vars.project_name, request.vars.project_website],
                        request.utcnow,
                        msgs,
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
            else:
                fieldValues = [request.vars[field] for field in fields]

            (good, obj_idNew) = Record.update(
                tp, obj_id, myId, fields, fieldValues, request.utcnow, msgs
            )
            if not good:
                break
            obj_id = obj_idNew
        else:
            good = True

    record = Record.make(tp, table, fields, obj_id, good, msgs)

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


def querysharing():
    session.forget(response)
    msgs = []
    good = False
    modDates = {}
    modCls = {}
    extra = {}
    for x in [1]:
        query_id = Check.isId("query_id", "q", "query", msgs)
        if query_id is None:
            break
        fieldName = request.vars.fname
        val = request.vars.val
        vr = request.vars.version
        if fieldName is None or fieldName not in {"is_shared", "is_published"}:
            msgs.append("error", "Illegal field name {fieldName}")
            break
        (authorized, msg) = Query.authWrite(query_id)
        if not authorized:
            msgs.append(("error", msg))
            break
        now = request.utcnow
        (good, modDates, modCls, extra) = QuerySave.putSharing(
            vr, query_id, fieldName, val, now, msgs
        )
    return dict(
        data=json.dumps(
            dict(msgs=msgs, good=good, modDates=modDates, modCls=modCls, extra=extra)
        )
    )


def queryupdate():
    session.forget(response)
    msgs = []
    good = False
    myId = auth.user.id if auth.user is not None else None
    fields = {}
    fieldsExe = {}
    vr = request.vars.version
    queryRecord = {}

    is_published = False
    is_shared = False

    for x in [1]:
        query_id = Check.isId("query_id", "q", "query", msgs)
        if query_id is None:
            break
        (authorized, msg) = Query.authWrite(query_id)
        if not authorized:
            msgs.append(("error", msg))
            break

        QuerySave.verifyVersion(vr, query_id)
        recordOld = Query.getBasicInfo(vr, query_id)

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
                fields["name"] = valSql
                fields["modified_on"] = request.utcnow
            mqlNew = request.vars.mql
            if valsOld["mql"] != mqlNew:
                msgs.append(("warning", "query body modified"))
                valSql = Check.isMql("q", mqlNew, msgs)
                if valSql is None:
                    break
                fieldsExe["mql"] = valSql
                fieldsExe["modified_on"] = request.utcnow
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
            fields["description"] = valSql
            fields["modified_on"] = request.utcnow
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
                QuerySave.putSlots(vr, query_id, exeSlots, is_shared)
                fieldsExe["executed_on"] = request.utcnow
                fieldsExe["eversion"] = emdrosVersion
                nResultSlots = countSlots(exeSlots)
                fieldsExe["results"] = nResults
                fieldsExe["resultmonads"] = nResultSlots
                msgs.append(("good", "Query executed"))
            else:
                QuerySave.putSlots(vr, query_id, [], is_shared)
            msgs.extend(theseMsgs)
        QuerySave.putMeta(vr, query_id, fields, fieldsExe)
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
                query=queryRecord,
                emdrosVersionsOld=emdrosVersionsOld,
            )
        )
    )
