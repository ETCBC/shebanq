from books import BOOKS
from verses import VERSES
from viewsettings import VIEWSETTINGS
from word import WORD
from query import QUERY
from querychapter import QUERYCHAPTER
from querysave import QUERYSAVE
from querytree import QUERYTREE
from queryrecent import QUERYRECENT
from note import NOTE
from notesave import NOTESAVE
from notesupload import NOTESUPLOAD
from notetree import NOTETREE
from record import RECORD, RECORDQUERY
from materials import MATERIAL
from side import SIDE
from chart import CHART
from csvdata import CSVDATA


# controllers for the (toplevel) menu items


def text():
    session.forget(response)
    Books = BOOKS()
    ViewSettings = VIEWSETTINGS(Books)
    ViewSettings.initState()
    return ViewSettings.page()


def words():
    session.forget(response)
    Books = BOOKS()
    ViewSettings = VIEWSETTINGS(Books)
    ViewSettings.initState()
    Word = WORD()
    return Word.page(ViewSettings)


def queries():
    session.forget(response)
    Books = BOOKS()
    ViewSettings = VIEWSETTINGS(Books)
    ViewSettings.initState()
    Query = QUERY()
    return Query.page(ViewSettings)


def notes():
    session.forget(response)
    Books = BOOKS()
    ViewSettings = VIEWSETTINGS(Books)
    ViewSettings.initState()
    Note = NOTE(Books)
    return Note.page(ViewSettings)


# controllers for fetching record pages (record data in sidebar, occurrences in main)


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
        Query = QUERY()
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


# controllers for fetching parts of the page


def material():
    session.forget(response)
    Books = BOOKS()
    Word = WORD()
    Query = QUERY()
    QueryChapter = QUERYCHAPTER()
    Note = NOTE(Books)
    RecordQuery = RECORDQUERY(Query)
    Material = MATERIAL(RecordQuery, Word, Query, QueryChapter, Note)
    return Material.page()


def sidematerial():
    session.forget(response)
    Books = BOOKS()
    Word = WORD()
    Query = QUERY()
    QueryChapter = QUERYCHAPTER()
    Note = NOTE(Books)
    RecordQuery = RECORDQUERY(Query)
    Material = MATERIAL(RecordQuery, Word, Query, QueryChapter, Note)
    Side = SIDE(Material, Word, Query, Note)
    return Side.page()


def sidewordbody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "word", extension="", vars=request.vars))
    Word = WORD()
    return Word.body()


def sidequerybody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "query", extension="", vars=request.vars))
    Query = QUERY()
    return Query.body()


def sidenotebody():
    session.forget(response)
    if not request.ajax:
        redirect(URL("hebrew", "note", extension="", vars=request.vars))
    Books = BOOKS()
    Note = NOTE(Books)
    return Note.body()


def sideword():
    session.forget(response)
    Record = RECORD()
    return Record.body()


def sidequery():
    session.forget(response)
    Record = RECORD()
    return Record.body()


def sidenote():
    session.forget(response)
    Record = RECORD()
    return Record.body()


# controllers for fetching parts of the queries and notes pages


def queriesr():
    session.forget(response)
    QueryRecent = QUERYRECENT()
    return QueryRecent.recent()


def querytree():
    session.forget(response)
    QueryTree = QUERYTREE()
    return QueryTree.get()


def notetree():
    session.forget(response)
    NoteTree = NOTETREE()
    return NoteTree.get()


def getversenotes():
    session.forget(response)
    Books = BOOKS()
    Note = NOTE(Books)
    return Note.getVerseNotes()


def putversenotes():
    session.forget(response)
    Books = BOOKS()
    Note = NOTE(Books)
    NoteSave = NOTESAVE(Note)
    return NoteSave.putVerseNotes()


def noteupload():
    session.forget(response)
    Books = BOOKS()
    Note = NOTE(Books)
    NotesUpload = NOTESUPLOAD(Books, Note)
    return NotesUpload.upload()


# controller to get csv data of the occurrences of a record (word, query, noteset)


def item():
    session.forget(response)
    Word = WORD()
    Query = QUERY()
    RecordQuery = RECORDQUERY(Query)
    CsvData = CSVDATA(RecordQuery, Word, Query)
    return CsvData.page()


# controller to produce a chart of the occurrences of a record


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    Books = BOOKS()
    Word = WORD()
    Query = QUERY()
    Note = NOTE(Books)
    RecordQuery = RECORDQUERY(Query)
    Chart = CHART(Books, RecordQuery, Word, Query, Note)
    return Chart.page()


# controllers to update record data


def itemrecord():
    session.forget(response)
    Query = QUERY()
    RecordQuery = RECORDQUERY(Query)
    return RecordQuery.getItem()


def querysharing():
    session.forget(response)
    Query = QUERY()
    QueryChapter = QUERYCHAPTER()
    QuerySave = QUERYSAVE(Query, QueryChapter)
    return QuerySave.sharing()


def queryupdate():
    session.forget(response)
    Query = QUERY()
    QueryChapter = QUERYCHAPTER()
    QuerySave = QUERYSAVE(Query, QueryChapter)
    return QuerySave.putRecord()


# controllers to get other data


def books():
    Books = BOOKS()
    session.forget(response)
    return Books.getNames()


def verse():
    session.forget(response)
    Verses = VERSES()
    return Verses.get()
