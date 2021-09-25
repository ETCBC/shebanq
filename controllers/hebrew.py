#!/usr/bin/env python

from gluon.custom_import import track_changes

import collections  # noqa F401

# needed for views

from viewdefs import (
    colorPicker,
    TP_LABELS,
    TR_INFO,
    TR_LABELS,
    TAB_VIEWS,
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

Check = CHECK(request, db)
Caching = CACHING(cache)
Pieces = Pieces(Check, Caching, auth, PASSAGE_DBS)
Word = WORD(Check, Caching, PASSAGE_DBS, VERSIONS)
Query = QUERY(Check, Caching, auth, db, VERSIONS)
QuerySave = QUERYSAVE(Check, Caching, Query, auth, db, VERSIONS)
QueryTree = QUERYTREE(auth, db, VERSION_ORDER, VERSION_INDEX)
QueryRecent = QUERYRECENT(db)
Note = NOTE(Check, Caching, Pieces, auth, db, NOTE_DB)
NoteSave = NOTESAVE(Caching, NOTE_DB)
NotesUpload = NOTESUPLOAD(Caching, Pieces, auth, db, NOTE_DB, VERSIONS)
NoteTree = NOTETREE(auth, NOTE_DB, VERSION_ORDER, VERSION_INDEX)
QueryChapter = QUERYCHAPTER(Caching, db, PASSAGE_DBS)
Record = RECORD(Check, Query, QuerySave, auth, db, LOAD)
Material = MATERIAL(
    Check, Caching, Record, Word, Query, QueryChapter, Note, PASSAGE_DBS
)
Side = SIDE(Check, Caching, Material, Word, Query, Note)
Chart = CHART(Check, Caching, Pieces, Record, Word, Query, Note, PASSAGE_DBS)
CsvData = CSVDATA(Check, Record, Word, Query, auth, PASSAGE_DBS)

Pieces.dep(Note, NoteSave)
Query.dep(QuerySave)
QuerySave.dep(QueryChapter)
Note.dep(NotesUpload)

track_changes(True)


def makeView(dummy=True):
    return VIEWSETTINGS(Check, Pieces, request, response, URL, VERSIONS)


def text():
    session.forget(response)

    return dict(
        ViewSettings=makeView(),
        colorPicker=colorPicker,
        legend=LEGEND,
        TP_LABELS=TP_LABELS,
        TAB_VIEWS=TAB_VIEWS,
        TR_LABELS=TR_LABELS,
        TR_INFO=TR_INFO,
    )


def material():
    session.forget(response)
    return Material.page()


def sidematerial():
    session.forget(response)
    return Side.page()


def sidewordbody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "word", extension="", vars=request.vars))
    return Word.body()


def sidequerybody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "query", extension="", vars=request.vars))
    return Query.body()


def sidenotebody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "note", extension="", vars=request.vars))
    return Note.body()


def sideword():
    session.forget(response)
    return Record.body()


def sidequery():
    session.forget(response)
    return Record.body()


def sidenote():
    session.forget(response)
    return Record.body()


def word():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "w"
    request.vars["page"] = 1
    return text()


def query():
    session.forget(response)
    request.vars["mr"] = "r"
    request.vars["qw"] = "q"
    if request.extension == "json":
        return Query.bodyJson()
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
    return Word.page(makeView())


def queries():
    session.forget(response)
    return Query.page(makeView())


def notes():
    session.forget(response)
    return Note.page(makeView())


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
    return Pieces.getBookTitles()


def verse():
    session.forget(response)
    if request.extension == "json":
        return Pieces.getVerseJson()
    return Pieces.getVerse()


def versenotes():
    session.forget(response)
    return Pieces.getVerseNotes(request.post_vars, request.utcnow)


def item():
    session.forget(response)
    return CsvData.page()


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    return Chart.page()


def noteupload():
    session.forget(response)
    return NotesUpload.upload(request.vars.file, request.utcnow)


def itemrecord():
    session.forget(response)
    return Record.getItem(request.vars, request.utcnow)


def querysharing():
    session.forget(response)
    return QuerySave.sharing(request.vars, request.utcnow)


def queryupdate():
    session.forget(response)
    return QuerySave.putRecord(request.vars, request.utcnow)
