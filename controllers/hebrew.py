#!/usr/bin/env python

# controllers for the (toplevel) menu items


def text():
    session.forget(response)
    ViewSettings.initState()
    return ViewSettings.page()


def words():
    session.forget(response)
    ViewSettings.initState()
    return Word.page()


def queries():
    session.forget(response)
    ViewSettings.initState()
    return Query.page()


def notes():
    session.forget(response)
    ViewSettings.initState()
    return Note.page()


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
# these controllers need not run ViewSettings


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


# controllers for fetching parts of the queries and notes pages


def queriesr():
    session.forget(response)
    return QueryRecent.recent()


def querytree():
    session.forget(response)
    return QueryTree.get(request.utcnow)


def notetree():
    session.forget(response)
    return NoteTree.get(request.utcnow)


def versenotes():
    session.forget(response)
    return Pieces.getVerseNotes(request.post_vars, request.utcnow)


def noteupload():
    session.forget(response)
    return NotesUpload.upload(request.vars.file, request.utcnow)


# controller to get csv data of the occurrences of a record (word, query, noteset)


def item():
    session.forget(response)
    return CsvData.page()


# controller to produce a chart of the occurrences of a record


def chart():  # controller to produce a chart of query results or lexeme occurrences
    session.forget(response)
    return Chart.page()


# controllers to update record data


def itemrecord():
    session.forget(response)
    return Record.getItem(request.vars, request.utcnow)


def querysharing():
    session.forget(response)
    return QuerySave.sharing(request.vars, request.utcnow)


def queryupdate():
    session.forget(response)
    return QuerySave.putRecord(request.vars, request.utcnow)


# controllers to get other data


def books():
    session.forget(response)
    return Pieces.getBookTitles()


def verse():
    session.forget(response)
    if request.extension == "json":
        return Pieces.getVerseJson()
    return Pieces.getVerse()
