import collections
import json

from constants import PUBLISH_FREEZE
from helpers import iEncode, iDecode, normRanges


class NOTE:
    def __init__(self, Check, Caching, Pieces, auth, db, NOTE_DB):
        self.Check = Check
        self.Caching = Caching
        self.Pieces = Pieces
        self.auth = auth
        self.db = db
        self.NOTE_DB = NOTE_DB

    def dep(self, NotesUpload):
        self.NotesUpload = NotesUpload

    def page(self, ViewSettings):
        Check = self.Check
        NotesUpload = self.NotesUpload

        key_id = Check.isId("goto", "n", "note", [])

        (authorized, myId, msg) = NotesUpload.authUpload()
        return dict(
            ViewSettings=ViewSettings,
            key_id=key_id,
            mayUpload=authorized,
            user_id=myId,
        )

    def body(self):
        Check = self.Check

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
        NOTE_DB = self.NOTE_DB

        bk = book["name"]
        ch = chapter["chapter_num"]
        if is_published == "x":
            isPubVersion = ""
        else:
            isPubVersion = " and is_published = 'T'"
        sql = f"""
select
    note.created_by,
    shebanq_web.auth_user.first_name,
    shebanq_web.auth_user.last_name,
    note.keywords,
    note.verse,
    note.is_published
from note
inner join shebanq_web.auth_user on shebanq_web.auth_user.id = created_by
where version = '{vr}' and book = '{bk}' and chapter = {ch} {isPubVersion}
order by note.verse
;
"""
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
        auth = self.auth
        Caching = self.Caching
        Pieces = self.Pieces
        NOTE_DB = self.NOTE_DB

        clauseAtomFirst = Caching.get(
            f"clause_atom_f_{vr}_", lambda: Pieces.getClauseAtomFirstSlot(vr), None
        )
        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = "" if myId is None else f" or created_by = {myId} "
        sql = f"""
select book, clause_atom from note
where keywords like '% {keywordsSql} %'
and version = '{vr}' and (is_shared = 'T' {extra})
;
"""
        clauseAtoms = NOTE_DB.executesql(sql)
        slots = {clauseAtomFirst[x[0]][x[1]] for x in clauseAtoms}
        return normRanges(None, fromset=slots)

    def getInfo(self, iidRep, vr, msgs):
        db = self.db

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
        sql = f"""
select first_name, last_name from auth_user where id = '{iid}'
;
"""
        uinfo = db.executesql(sql)
        if uinfo is not None and len(uinfo) > 0:
            nRecord["first_name"] = uinfo[0][0]
            nRecord["last_name"] = uinfo[0][1]
        return nRecord

    def countNotes(self, user_id, keywords):
        auth = self.auth
        NOTE_DB = self.NOTE_DB

        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = f" or created_by = {user_id} " if myId == user_id else ""
        sql = f"""
select
    version,
    count(id) as amount
from note
where keywords like '% {keywordsSql} %' and (is_shared = 'T' {extra})
group by version
;"""
        records = NOTE_DB.executesql(sql)
        vrs = set()
        versionInfo = {}
        for (vr, amount) in records:
            vrs.add(vr)
            versionInfo[vr] = dict(n=amount)
        return versionInfo

    def inVerse(
        self, vr, bk, ch, vs, myId, clauseAtoms, changed, now, msgs, authenticated, edit
    ):
        NOTE_DB = self.NOTE_DB

        condition = "note.is_shared = 'T' or note.is_published = 'T' "
        if myId is not None:
            condition += f" or note.created_by = {myId} "

        noteSql = f"""
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
