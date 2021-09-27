from gluon import current

from pieces import PIECES
from viewdefs import VIEWDEFS
from viewsettings import VIEWSETTINGS
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


current.ViewDefs = VIEWDEFS()
current.URL = URL
current.LOAD = LOAD

Pieces = PIECES()
ViewSettings = VIEWSETTINGS(Pieces)
Word = WORD(ViewSettings)
Query = QUERY(ViewSettings)
QuerySave = QUERYSAVE(Query)
QueryTree = QUERYTREE()
QueryRecent = QUERYRECENT()
Note = NOTE(ViewSettings, Pieces)
NoteSave = NOTESAVE()
NotesUpload = NOTESUPLOAD(Pieces)
NoteTree = NOTETREE()
QueryChapter = QUERYCHAPTER()
Record = RECORD(Query, QuerySave)
Material = MATERIAL(Record, Word, Query, QueryChapter, Note)
Side = SIDE(ViewSettings, Material, Word, Query, Note)
Chart = CHART(Pieces, Record, Word, Query, Note)
CsvData = CSVDATA(Record, Word, Query)

Pieces.alsoDependentOn(Note, NoteSave)
Query.alsoDependentOn(QuerySave)
QuerySave.alsoDependentOn(QueryChapter)
Note.alsoDependentOn(NotesUpload)
