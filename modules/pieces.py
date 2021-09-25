import json

from blang import BOOK_LANGS, BOOK_TRANS, BOOK_NAMES
from verse import Verse


class Pieces:
    def __init__(self, Check, Caching, auth, PASSAGE_DBS):
        self.Check = Check
        self.Caching = Caching
        self.auth = auth
        self.PASSAGE_DBS = PASSAGE_DBS

    def dep(self, Note, NoteSave):
        self.Note = Note
        self.NoteSave = NoteSave

    def getBookTitles(self):
        jsinit = f"""
var bookLatin = {json.dumps(BOOK_NAMES["Hebrew"]["la"])};
var bookTrans = {json.dumps(BOOK_TRANS)};
var bookLangs = {json.dumps(BOOK_LANGS["Hebrew"])};
"""
        return dict(jsinit=jsinit)

    def getBooks(self, vr):
        Caching = self.Caching

        return Caching.get(f"books_{vr}_", lambda: self.getBooks_c(vr), None)

    def getBooks_c(self, vr):
        # get book information: number of chapters per book
        PASSAGE_DBS = self.PASSAGE_DBS

        if vr in PASSAGE_DBS:
            booksData = PASSAGE_DBS[vr].executesql(
                """
select book.id, book.name, max(chapter_num)
from chapter inner join book
on chapter.book_id = book.id group by name order by book.id
;
"""
            )
            booksOrder = [x[1] for x in booksData]
            books = dict((x[1], x[2]) for x in booksData)
            bookIds = dict((x[1], x[0]) for x in booksData)
            bookName = dict((x[0], x[1]) for x in booksData)
            result = (books, booksOrder, bookIds, bookName)
        else:
            result = ({}, [], {}, {})
        return result

    def getVerseJson(self, vr, bk, ch, vs):
        Caching = self.Caching

        return Caching.get(
            f"versej_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.getVerseJson_c(vr, bk, ch, vs),
            None,
        )

    def getVerseJson_c(self):
        Check = self.Check
        PASSAGE_DBS = self.PASSAGE_DBS

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")

        passageDb = PASSAGE_DBS[vr] if vr in PASSAGE_DBS else None
        msgs = []
        good = True
        data = dict()
        if passageDb is None:
            msgs.append(("Error", f"No such version: {vr}"))
            good = False
        if good:
            verseInfo = passageDb.executesql(
                f"""
select verse.id, verse.text from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
where book.name = '{bk}' and chapter.chapter_num = {ch} and verse_num = {vs}
;
"""
            )
            if len(verseInfo) == 0:
                msgs.append(("Error", f"No such verse: {bk} {ch}:{vs}"))
                good = False
            else:
                data = verseInfo[0]
                vid = data[0]
                wordInfo = passageDb.executesql(
                    f"""
select word.word_phono, word.word_phono_sep
from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
where verse.id = {vid}
order by word_number
;
"""
                )
                data = dict(
                    text=data[1], phonetic="".join(x[0] + x[1] for x in wordInfo)
                )
        return json.dumps(dict(good=good, msgs=msgs, data=data), ensure_ascii=False)

    def getVerse(self):
        Check = self.Check
        Caching = self.Caching

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")
        tr = Check.field("material", "", "tr")

        if vs is None:
            return dict(good=False, msgs=[])

        return Caching.get(
            f"verse_{vr}_{bk}_{ch}_{vs}_{tr}_",
            lambda: self.getVerse_c(vr, bk, ch, vs, tr),
            None,
        )

    def getVerse_c(self, vr, bk, ch, vs, tr):
        PASSAGE_DBS = self.PASSAGE_DBS

        material = Verse(
            PASSAGE_DBS,
            vr,
            bk,
            ch,
            vs,
            xml=None,
            wordData=None,
            tp="txtd",
            tr=tr,
            mr=None,
        )
        good = True
        msgs = []
        if len(material.wordData) == 0:
            msgs = [("error", f"{bk} {ch}:{vs} does not exist")]
            good = False
        return dict(
            good=good,
            msgs=msgs,
            material=material,
        )

    def getVerseNotes(self, requestVars, now):
        Check = self.Check
        Note = self.Note
        NoteSave = self.NoteSave
        auth = self.auth

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")
        edit = Check.isBool("edit")
        save = Check.isBool("save")

        myId = None
        if auth.user:
            myId = auth.user.id
        authenticated = myId is not None

        clauseAtoms = self.getClauseAtoms(vr, bk, ch, vs)
        changed = False

        msgs = []

        if save:
            if myId is None:
                msgs.append(("error", "You have to be logged in when you save notes"))
            else:
                notes = (
                    json.loads(requestVars.notes)
                    if requestVars and requestVars.notes
                    else []
                )
                changed = NoteSave.put(
                    myId, vr, bk, ch, vs, now, notes, clauseAtoms, msgs
                )
        return Note.inVerse(
            vr, bk, ch, vs, myId, clauseAtoms, changed, now, msgs, authenticated, edit
        )

    def getClauseAtomFirstSlot(self, vr):
        Caching = self.Caching

        return Caching.get(
            f"clause_atom_f_{vr}_",
            lambda: self.getClauseAtomFirstSlot_c(vr),
            None,
        )

    def getClauseAtomFirstSlot_c(self, vr):
        PASSAGE_DBS = self.PASSAGE_DBS

        (books, booksOrder, bookIds, bookName) = self.getBooks(vr)
        sql = """
select book_id, ca_num, first_m
from clause_atom
;
"""
        caData = PASSAGE_DBS[vr].executesql(sql) if vr in PASSAGE_DBS else []
        caFirst = {}
        for (book_id, ca_num, first_m) in caData:
            book_name = bookName[book_id]
            caFirst.setdefault(book_name, {})[ca_num] = first_m
        return caFirst

    def getClauseAtoms(self, vr, bk, ch, vs):
        Caching = self.Caching
        return Caching.get(
            f"clause_atoms_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.getClauseAtoms_c(vr, bk, ch, vs),
            None,
        )

    def getClauseAtoms_c(self, vr, bk, ch, vs):
        # get clauseatoms for each verse
        PASSAGE_DBS = self.PASSAGE_DBS

        clauseAtoms = []
        caData = (
            PASSAGE_DBS[vr].executesql(
                f"""
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
    book.name = '{bk}' and chapter.chapter_num = {ch} and verse.verse_num = {vs}
order by
    word.clause_atom_number
;
"""
            )
            if vr in PASSAGE_DBS
            else []
        )

        for (ca_num,) in caData:
            clauseAtoms.append(ca_num)
        return clauseAtoms
