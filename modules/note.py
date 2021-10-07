import collections
import json
from textwrap import dedent

from gluon import current

from constants import PUBLISH_FREEZE
from helpers import iEncode, iDecode, normRanges


class NOTE:
    """Handles notes.
    """
    def __init__(self, Books):
        self.Books = Books

    def authUpload(self):
        auth = current.auth
        db = current.db

        myId = None
        authorized = False
        if auth.user:
            myId = auth.user.id
        if myId:
            sql = dedent(
                f"""
                select uid from uploaders where uid = {myId}
                """
            )
            records = db.executesql(sql)
            authorized = (
                records is not None and len(records) == 1 and records[0][0] == myId
            )
        msg = "" if authorized else "you are not allowed to upload notes as csv files"
        return (authorized, myId, msg)

    def page(self, ViewSettings):
        Check = current.Check

        pageConfig = ViewSettings.writeConfig()

        key_id = Check.isId("goto", "n", "note", [])

        (authorized, myId, msg) = self.authUpload()
        return dict(
            pageConfig=pageConfig,
            key_id=key_id,
            mayUpload=authorized,
            user_id=myId,
        )

    def getVerseNotes(self):
        """Get the notes belonging to a single verse.

        Reads request parameters to determine which verse.
        """
        Check = current.Check
        auth = current.auth

        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        vs = Check.field("material", "", "verse")
        edit = Check.isBool("edit")

        myId = None
        if auth.user:
            myId = auth.user.id
        authenticated = myId is not None

        clauseAtoms = self.getClauseAtoms(vr, bk, ch, vs)
        changed = False

        msgs = []

        return self.inVerse(
            vr, bk, ch, vs, myId, clauseAtoms, changed, msgs, authenticated, edit
        )

    def body(self):
        """Retrieves a note set record based on parameters.
        """
        Check = current.Check

        vr = Check.field("material", "", "version")
        iidRep = Check.field("material", "", "iid")

        (iid, keywords) = iDecode("n", iidRep)
        msgs = []
        if not iid:
            msg = f"Not a valid note id: {iid}"
            msgs.append(("error", msg))
            return dict(
                noteRecord=dict(),
                note=json.dumps(dict()),
                msgs=json.dumps(msgs),
            )
        noteRecord = self.getInfo(iidRep, vr, msgs)
        return dict(
            vr=vr,
            noteRecord=noteRecord,
            note=json.dumps(noteRecord),
            msgs=json.dumps(msgs),
        )

    def getItems(self, vr, book, chapter, is_published):
        NOTE_DB = current.NOTE_DB

        bk = book["name"]
        ch = chapter["chapter_num"]
        if is_published == "x":
            isPubVersion = ""
        else:
            isPubVersion = " and is_published = 'T'"
        sql = dedent(
            f"""
            select
                note.created_by,
                shebanq_web.auth_user.first_name,
                shebanq_web.auth_user.last_name,
                note.keywords,
                note.verse,
                note.is_published
            from note
            inner join shebanq_web.auth_user
            on shebanq_web.auth_user.id = created_by
            where
                version = '{vr}' and
                book = '{bk}' and chapter = {ch} {isPubVersion}
            order by note.verse
            ;
            """
        )
        records = NOTE_DB.executesql(sql)
        user = {}
        nPublished = collections.Counter()
        nNotes = collections.Counter()
        nVerses = {}
        for (user_id, first_name, last_name, keywords, v, is_published) in records:
            if user_id not in user:
                user[user_id] = (first_name, last_name)
            for keyword in set(keywords.strip().split()):
                if is_published == "T":
                    nPublished[(user_id, keyword)] += 1
                nNotes[(user_id, keyword)] += 1
                nVerses.setdefault((user_id, keyword), set()).add(v)
        r = []
        for (user_id, keyword) in nNotes:
            (first_name, last_name) = user[user_id]
            thisNPub = nPublished[(user_id, keyword)]
            thisNNotes = nNotes[(user_id, keyword)]
            thisNVerses = len(nVerses[(user_id, keyword)])
            r.append(
                {
                    "item": dict(
                        id=iEncode("n", user_id, keyword),
                        first_name=first_name,
                        last_name=last_name,
                        keywords=keyword,
                        is_published=thisNPub > 0,
                        nNotes=thisNNotes,
                        nVerses=thisNVerses,
                    ),
                    "slots": json.dumps([]),
                }
            )
        return r

    def read(self, vr, iid, keywords):
        auth = current.auth
        Caching = current.Caching
        NOTE_DB = current.NOTE_DB

        clauseAtomFirst = Caching.get(
            f"clause_atom_f_{vr}_", lambda: self.getClauseAtomFirstSlot(vr), None
        )
        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = "" if myId is None else f" or created_by = {myId} "
        sql = dedent(
            f"""
            select book, clause_atom from note
            where keywords like '% {keywordsSql} %'
            and version = '{vr}' and (is_shared = 'T' {extra})
            ;
            """
        )
        clauseAtoms = NOTE_DB.executesql(sql)
        slots = {clauseAtomFirst[x[0]][x[1]] for x in clauseAtoms}
        return normRanges(None, fromset=slots)

    def getClauseAtoms(self, vr, bk, ch, vs):
        Caching = current.Caching
        return Caching.get(
            f"clause_atoms_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.getClauseAtoms_c(vr, bk, ch, vs),
            None,
        )

    def getClauseAtoms_c(self, vr, bk, ch, vs):
        PASSAGE_DBS = current.PASSAGE_DBS

        clauseAtoms = []
        caData = (
            PASSAGE_DBS[vr].executesql(
                dedent(
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
                        book.name = '{bk}' and
                        chapter.chapter_num = {ch} and
                        verse.verse_num = {vs}
                    order by
                        word.clause_atom_number
                    ;
                    """
                )
            )
            if vr in PASSAGE_DBS
            else []
        )

        for row in caData:
            clauseAtoms.append(row[0])
        return clauseAtoms

    def getClauseAtomFirstSlot(self, vr):
        Caching = current.Caching

        return Caching.get(
            f"clause_atom_f_{vr}_",
            lambda: self.getClauseAtomFirstSlot_c(vr),
            None,
        )

    def getClauseAtomFirstSlot_c(self, vr):
        Books = self.Books
        PASSAGE_DBS = current.PASSAGE_DBS

        (books, booksOrder, bookIds, bookName) = Books.get(vr)
        sql = dedent(
            """
            select book_id, ca_num, first_m
            from clause_atom
            ;
            """
        )
        caData = PASSAGE_DBS[vr].executesql(sql) if vr in PASSAGE_DBS else []
        caFirst = {}
        for (book_id, ca_num, first_m) in caData:
            book_name = bookName[book_id]
            caFirst.setdefault(book_name, {})[ca_num] = first_m
        return caFirst

    def getInfo(self, iidRep, vr, msgs):
        db = current.db

        (iid, keywords) = iDecode("n", iidRep)
        if iid is None:
            return {}
        nRecord = dict(
            id=iidRep,
            user_id=iid,
            first_name="N?",
            last_name="N?",
            keywords=keywords,
            versions={},
        )
        nRecord["versions"] = self.countNotes(iid, keywords)
        sql = dedent(
            f"""
            select first_name, last_name from auth_user where id = '{iid}'
            ;
            """
        )
        uinfo = db.executesql(sql)
        if uinfo is not None and len(uinfo) > 0:
            nRecord["first_name"] = uinfo[0][0]
            nRecord["last_name"] = uinfo[0][1]
        return nRecord

    def countNotes(self, user_id, keywords):
        auth = current.auth
        NOTE_DB = current.NOTE_DB

        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = f" or created_by = {user_id} " if myId == user_id else ""
        sql = dedent(
            f"""
            select
                version,
                count(id) as amount
            from note
            where
                keywords like '% {keywordsSql} %' and
                (is_shared = 'T' {extra})
            group by version
            ;
            """
        )
        records = NOTE_DB.executesql(sql)
        vrs = set()
        versionInfo = {}
        for (vr, amount) in records:
            vrs.add(vr)
            versionInfo[vr] = dict(n=amount)
        return versionInfo

    def inVerse(
        self, vr, bk, ch, vs, myId, clauseAtoms, changed, msgs, authenticated, edit
    ):
        NOTE_DB = current.NOTE_DB

        condition = "note.is_shared = 'T' or note.is_published = 'T' "
        if myId is not None:
            condition += f" or note.created_by = {myId} "

        noteSql = dedent(
            f"""
            select
                note.id,
                note.created_by as user_id,
                shebanq_web.auth_user.first_name,
                shebanq_web.auth_user.last_name,
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
                ({condition})
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
            """
        )

        records = NOTE_DB.executesql(noteSql)
        users = {}
        keyIndex = {}
        notesProto = collections.defaultdict(lambda: {})
        clauseAtomUsers = collections.defaultdict(lambda: collections.OrderedDict())
        if myId is not None and edit:
            users[myId] = "me"
            for clauseAtom in clauseAtoms:
                notesProto[clauseAtom][myId] = [
                    dict(
                        user_id=myId,
                        note_id=0,
                        is_shared=True,
                        is_published=False,
                        status="o",
                        keywords="",
                        ntext="",
                    )
                ]
                clauseAtomUsers[clauseAtom][myId] = None
        good = True
        if records is None:
            msgs.append(
                (
                    "error",
                    f"Cannot lookup notes for {bk} {ch}:{vs} in version {vr}",
                )
            )
            good = False
        elif len(records) == 0:
            msgs.append(("warning", "No notes"))
        else:
            now = current.request.utcnow

            for (
                note_id,
                user_id,
                first_name,
                last_name,
                clause_atom,
                is_shared,
                is_published,
                published_on,
                status,
                keywords,
                ntext,
            ) in records:
                if (
                    myId is None or (user_id != myId) or not edit
                ) and user_id not in users:
                    users[user_id] = f"{first_name} {last_name}"
                if user_id not in clauseAtomUsers[clause_atom]:
                    clauseAtomUsers[clause_atom][user_id] = None
                is_published = is_published == "T"
                is_shared = is_published or is_shared == "T"
                ro = (
                    myId is None
                    or user_id != myId
                    or not edit
                    or (
                        is_published
                        and published_on is not None
                        and (published_on <= now - PUBLISH_FREEZE)
                    )
                )
                keywordList = keywords.strip().split()
                for keyword in keywordList:
                    keyIndex[f"{user_id} {keyword}"] = iEncode(
                        "n", user_id, keywords=keyword
                    )
                notesProto.setdefault(clause_atom, {}).setdefault(user_id, []).append(
                    dict(
                        user_id=user_id,
                        note_id=note_id,
                        ro=ro,
                        is_shared=is_shared,
                        is_published=is_published,
                        status=status,
                        keywords=keywords,
                        ntext=ntext,
                    )
                )
        notes = {}
        for clauseAtom in notesProto:
            for user_id in clauseAtomUsers[clauseAtom]:
                notes.setdefault(clauseAtom, []).extend(notesProto[clauseAtom][user_id])

        return json.dumps(
            dict(
                good=good,
                changed=changed,
                msgs=msgs,
                users=users,
                notes=notes,
                keyIndex=keyIndex,
                authenticated=authenticated,
            )
        )
