import collections
import json

from constants import PUBLISH_FREEZE
from viewdefs import NOTE_STATUS_CLS
from helpers import (
    iEncode,
    iDecode,
    normRanges,
)


class NOTE:
    def __init__(
        self,
        Caching,
        Chunk,
        auth,
        db,
        NOTE_DB,
        VERSIONS,
    ):
        self.Caching = Caching
        self.auth = auth
        self.db = db
        self.NOTE_DB = NOTE_DB
        self.VERSIONS = VERSIONS

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

    def load(self, vr, iid, keywords):
        auth = self.auth
        Caching = self.Caching
        Chunk = self.Chunk
        NOTE_DB = self.NOTE_DB

        clauseAtomFirst = Caching.get(
            f"clause_atom_f_{vr}_", lambda: Chunk.getClauseAtomFirstSlot(vr), None
        )
        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = "" if myId is None else f""" or created_by = {myId} """
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
        NOTE_DB = self.notedb

        keywordsSql = keywords.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = f""" or created_by = {user_id} """ if myId == user_id else ""
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

    def save(self, myId, vr, bk, ch, vs, now, notes, clauseAtoms, msgs):
        Caching = self.Caching
        NOTE_DB = self.NOTE_DB

        (good, notesOld, notesUpd, notesNew, notesDel) = self.filter(
            myId, notes, clauseAtoms, msgs
        )

        updated = 0
        for note_id in notesUpd:
            (is_shared, is_published, status, keywords, ntext) = notesUpd[note_id]
            (isSharedOld, isPubOld, statusOld, keywordsOld, ntextOld) = notesOld[
                note_id
            ]
            extrafields = []
            if is_shared and not isSharedOld:
                extrafields.append(f",\n\tshared_on = '{now}'")
            if not is_shared and isSharedOld:
                extrafields.append(",\n\tshared_on = null")
            if is_published and not isPubOld:
                extrafields.append(f",\n\tpublished_on = '{now}'")
            if not is_published and isPubOld:
                extrafields.append(",\n\tpublished_on = null")
            is_shared = "'T'" if is_shared else "null"
            is_published = "'T'" if is_published else "null"
            status = "o" if status not in {"o", "*", "+", "?", "-", "!"} else status
            updateSql = f"""
update note
    set modified_on = '{now}',
    is_shared = {is_shared},
    is_published = {is_published},
    status = '{status}',
    keywords = '{keywords.replace("'", "''")}',
    ntext = '{ntext.replace("'", "''")}'{"".join(extrafields)}
where id = {note_id}
;
"""
            NOTE_DB.executesql(updateSql)
            updated += 1
        if len(notesDel) > 0:
            deleteSql = f"""
delete from note where id in ({",".join(str(x) for x in notesDel)})
;
"""
            NOTE_DB.executesql(deleteSql)

        for clause_atom in notesNew:
            (is_shared, is_published, status, keywords, ntext) = notesNew[clause_atom]
            sh = "'T'" if is_shared else "null"
            sht = f"'{now}'" if is_shared else "null"
            pb = "'T'" if is_published else "null"
            pbt = "'{now}'" if is_published else "null"
            fl = "o" if status not in {"o", "*", "+", "?", "-", "!"} else status
            keywordsSql = keywords.replace("'", "''")
            ntr = ntext.replace("'", "''")
            insertSql = f"""
insert into note
(version, book, chapter, verse, clause_atom,
created_by, created_on, modified_on,
is_shared, shared_on, is_published, published_on,
status, keywords, ntext)
values
('{vr}', '{bk}', {ch}, {vs}, {clause_atom},
 {myId}, '{now}', '{now}', {sh}, {sht}, {pb}, {pbt},
 '{fl}', '{keywordsSql}', '{ntr}')
;
"""
            NOTE_DB.executesql(insertSql)

        changed = False
        if len(notesDel) > 0:
            msgs.append(("special", f"Deleted notes: {len(notesDel)}"))
        if updated > 0:
            msgs.append(("special", f"Updated notes: {updated}"))
        if len(notesNew) > 0:
            msgs.append(("special", f"Added notes: {len(notesNew)}"))
        if len(notesDel) + len(notesNew) + updated == 0:
            msgs.append(("warning", "No changes"))
        else:
            changed = True
            Caching.clear(f"^items_n_{vr}_{bk}_{ch}_")
            if len(notesNew):
                for keywords in {notesNew[clause_atom][3] for clause_atom in notesNew}:
                    Caching.clear(
                        f"^verses_{vr}_n_{iEncode('n', myId, keywords=keywords)}_",
                    )
            if len(notesDel):
                for note_id in notesDel:
                    if note_id in notesOld:
                        keywords = notesOld[note_id][3]
                        Caching.clear(
                            f"^verses_{vr}_n_{iEncode('n', myId, keywords=keywords)}_",
                        )
        return changed

    def filter(self, myId, notes, clauseAtoms, msgs):
        NOTE_DB = self.NOTE_DB

        good = True
        notesOther = set()
        notesMissing = set()
        notesExtra = set()
        notesSame = set()
        clauseErrors = set()
        emptyNew = 0
        notesOld = {}
        notesUpd = {}
        notesNew = {}
        notesDel = set()
        for fields in notes:
            note_id = int(fields["note_id"])
            user_id = int(fields["user_id"])
            clause_atom = int(fields["clause_atom"])
            if user_id != myId:
                notesOther.add(note_id)
                good = False
                continue
            if clause_atom not in clauseAtoms:
                clauseErrors.add(note_id)
                good = False
                continue
            keywords = "".join(
                " " + keyword + " " for keyword in fields["keywords"].strip().split()
            )
            ntext = fields["ntext"].strip()
            if keywords == "" and ntext == "":
                if note_id == 0:
                    emptyNew += 1
                else:
                    notesDel.add(note_id)
                continue
            if note_id != 0:
                notesUpd[note_id] = (
                    fields["is_shared"],
                    fields["is_published"],
                    fields["status"],
                    keywords,
                    ntext,
                )
            else:
                notesNew[fields["clause_atom"]] = (
                    fields["is_shared"],
                    fields["is_published"],
                    fields["status"],
                    keywords,
                    ntext,
                )
        if len(notesUpd) > 0 or len(notesDel) > 0:
            ids = ",".join(str(x) for x in (set(notesUpd.keys()) | notesDel))
            sqlOld = f"""
select id, created_by, is_shared, is_published, status, keywords, ntext
from note where id in ({ids})
;
"""
            cresult = NOTE_DB.executesql(sqlOld)
            if cresult is not None:
                for (
                    note_id,
                    user_id,
                    isSharedOld,
                    isPubOld,
                    statusOld,
                    keywordsOld,
                    ntextOld,
                ) in cresult:
                    remove = False
                    if user_id != myId:
                        notesOther.add(note_id)
                        remove = True
                    elif note_id not in notesUpd and note_id not in notesDel:
                        notesExtra.add(note_id)
                        remove = True
                    elif note_id in notesUpd:
                        (is_shared, is_published, status, keywords, ntext) = notesUpd[
                            note_id
                        ]
                        if not is_shared:
                            is_shared = None
                        if not is_published:
                            is_published = None
                        if (
                            statusOld == status
                            and keywordsOld == keywords
                            and ntextOld == ntext
                            and isSharedOld == is_shared
                            and isPubOld == is_published
                        ):
                            notesSame.add(note_id)
                            if note_id not in notesDel:
                                remove = True
                    if remove:
                        if note_id in notesUpd:
                            del notesUpd[note_id]
                        if note_id in notesDel:
                            notesDel.remove(note_id)
                    else:
                        notesOld[note_id] = (
                            isSharedOld,
                            isPubOld,
                            statusOld,
                            keywordsOld,
                            ntextOld,
                        )
        removable = set()
        for note_id in notesUpd:
            if note_id not in notesOld:
                if note_id not in notesOther:
                    notesMissing.add(note_id)
                    removable.add(note_id)
        for note_id in removable:
            del notesUpd[note_id]
        removable = set()
        for note_id in notesDel:
            if note_id not in notesOld:
                if note_id not in notesOther:
                    notesMissing.add(note_id)
                    removable.add(note_id)
        for note_id in removable:
            notesDel.remove(note_id)
        if len(notesOther) > 0:
            msgs.append(("error", f"Notes of other users skipped: {len(notesOther)}"))
        if len(notesMissing) > 0:
            msgs.append(("error", f"Non-existing notes: {len(notesMissing)}"))
        if len(notesExtra) > 0:
            msgs.append(("error", f"Notes not shown: {len(notesExtra)}"))
        if len(clauseErrors) > 0:
            msgs.append(
                ("error", f"Notes referring to wrong clause: {len(clauseErrors)}")
            )
        if len(notesSame) > 0:
            pass
        if emptyNew > 0:
            pass
        return (good, notesOld, notesUpd, notesNew, notesDel)

    def upload(self, user_id, filetext, now, msgs):
        Caching = self.Caching
        Chunk = self.Chunk
        NOTE_DB = self.NOTE_DB
        VERSIONS = self.VERSIONS

        myVersions = set()
        bookInfo = {}
        for vr in VERSIONS:
            myVersions.add(vr)
            bookInfo[vr] = Chunk.getBooks(vr)[0]
        normFields = "\t".join(
            """
            version
            book
            chapter
            verse
            clause_atom
            is_shared
            is_published
            status
            keywords
            ntext
        """.strip().split()
        )
        good = True
        fieldnames = normFields.split("\t")
        nfields = len(fieldnames)
        errors = {}
        allKeywords = set()
        allVersions = set()
        now = now
        created_on = now
        modified_on = now

        nerrors = 0
        chunks = []
        chunksize = 100
        sqlhead = f"""
insert into note
({", ".join(fieldnames)},
 created_by, created_on, modified_on, shared_on, published_on,
 bulk) values
"""
        thisChunk = []
        thisI = 0
        for (i, linenl) in enumerate(filetext.value.decode("utf8").split("\n")):
            line = linenl.rstrip()
            if line == "":
                continue
            if i == 0:
                if line != normFields:
                    msgs.append(
                        [
                            "error",
                            (
                                f"Wrong fields: {line}. "
                                f"Required fields are {normFields}"
                            ),
                        ]
                    )
                    good = False
                    break
                continue
            fields = line.replace("'", "''").split("\t")
            if len(fields) != nfields:
                nerrors += 1
                errors.setdefault("wrong number of fields", []).append(i + 1)
                continue
            (
                version,
                book,
                chapter,
                verse,
                clause_atom,
                is_shared,
                is_published,
                status,
                keywords,
                ntext,
            ) = fields
            published_on = "NULL"
            shared_on = "NULL"
            if version not in myVersions:
                nerrors += 1
                errors.setdefault("unrecognized version", []).append(
                    f"{i + 1}:{version}"
                )
                continue
            books = bookInfo[version]
            if book not in books:
                nerrors += 1
                errors.setdefault("unrecognized book", []).append(f"{i + 1}:{book}")
                continue
            maxChapter = books[book]
            if not chapter.isdigit() or int(chapter) > maxChapter:
                nerrors += 1
                errors.setdefault("unrecognized chapter", []).append(
                    f"{i + 1}:{chapter}"
                )
                continue
            if not verse.isdigit() or int(verse) > 200:
                nerrors += 1
                errors.setdefault("unrecognized verse", []).append(f"{i + 1}:{verse}")
                continue
            if not clause_atom.isdigit() or int(clause_atom) > 100000:
                nerrors += 1
                errors.setdefault("unrecognized clause_atom", []).append(
                    f"{i + 1}:{clause_atom}"
                )
                continue
            if is_shared not in {"T", ""}:
                nerrors += 1
                errors.setdefault("unrecognized shared field", []).append(
                    f"{i + 1}:{is_shared}"
                )
                continue
            if is_published not in {"T", ""}:
                nerrors += 1
                errors.setdefault("unrecognized published field", []).append(
                    f"{i + 1}:{is_published}"
                )
                continue
            if status not in NOTE_STATUS_CLS:
                nerrors += 1
                errors.setdefault("unrecognized status", []).append(f"{i + 1}:{status}")
                continue
            if len(keywords) >= 128:
                nerrors += 1
                errors.setdefault("keywords length over 128", []).append(
                    f"{i + 1}:{len(keywords)}"
                )
                continue
            if len(ntext) >= 1024:
                nerrors += 1
                errors.setdefault("note text length over 1024", []).append(
                    f"{i + 1}:{len(ntext)}"
                )
                continue
            if nerrors > 20:
                msgs.append(["error", "too many errors, aborting"])
                break
            if is_shared == "T":
                shared_on = f"'{now}'"
            if is_published == "T":
                published_on = f"'{now}'"
            keywordList = keywords.split()
            if len(keywordList) == 0:
                errors.setdefault("empty keyword", []).append(f'{i+ 1}:"{keywords}"')
                continue
            allKeywords |= set(keywordList)
            keywords = "".join(f" {x} " for x in keywordList)
            allVersions.add(version)
            thisChunk.append(
                (
                    f"('{version}','{book}',{chapter},{verse},{clause_atom},"
                    f"'{is_shared}','{is_published}',"
                    f"'{status}','{keywords}','{ntext}',{user_id},"
                    f"'{created_on}','{modified_on}',{shared_on},{published_on},'b')"
                )
            )
            thisI += 1
            if thisI >= chunksize:
                chunks.append(thisChunk)
                thisChunk = []
                thisI = 0
        if len(thisChunk):
            chunks.append(thisChunk)

        # with open('/tmp/xxx.txt', 'w') as fh:
        #    for line in filetext.value:
        #        fh.write(line)
        if errors or nerrors:
            good = False
        else:
            avrep = "', '".join(allVersions)
            whereVersion = f"version in ('{avrep}')"
            whereKeywords = " or ".join(
                f" keywords like '% {keyword} %' " for keyword in keywordList
            )
            # first delete previously bulk uploaded notes by this author
            # and with these keywords and these versions
            delSql = f"""delete from note
where bulk = 'b'
and created_by = {user_id}
and {whereVersion}
and {whereKeywords};"""
            NOTE_DB.executesql(delSql)
            for chunk in chunks:
                chunkRep = ",\n".join(chunk)
                sql = f"{sqlhead} {chunkRep};"
                NOTE_DB.executesql(sql)
            Caching.clear(r"^items_n_")
            for vr in myVersions:
                Caching.clear(f"^verses_{vr}_n_")
        for msg in sorted(errors):
            istr = ",".join(str(i) for i in errors[msg])
            msgs.append(["error", f"{msg}: {istr}"])
        msgs.append(["good" if good else "error", "Done"])
        return True

    def inVerse(
        self, vr, bk, ch, vs, myId, clauseAtoms, changed, now, msgs, loggedIn, edit
    ):
        NOTE_DB = self.NOTE_DB

        condition = """note.is_shared = 'T' or note.is_published = 'T' """
        if myId is not None:
            condition += f""" or note.created_by = {myId} """

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
                loggedIn=loggedIn,
            )
        )
