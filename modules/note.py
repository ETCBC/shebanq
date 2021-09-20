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

    def getItems(self, vr, book, chapter, pub):
        NOTE_DB = self.NOTE_DB

        bk = book["name"]
        ch = chapter["chapter_num"]
        if pub == "x":
            pubv = ""
        else:
            pubv = " and is_published = 'T'"
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
where version = '{vr}' and book = '{bk}' and chapter = {ch} {pubv}
order by note.verse
;
"""
        records = NOTE_DB.executesql(sql)
        user = {}
        npub = collections.Counter()
        nnotes = collections.Counter()
        nverses = {}
        for (uid, ufname, ulname, kw, v, pub) in records:
            if uid not in user:
                user[uid] = (ufname, ulname)
            for k in set(kw.strip().split()):
                if pub == "T":
                    npub[(uid, k)] += 1
                nnotes[(uid, k)] += 1
                nverses.setdefault((uid, k), set()).add(v)
        r = []
        for (uid, k) in nnotes:
            (ufname, ulname) = user[uid]
            thisNPub = npub[(uid, k)]
            thisNNotes = nnotes[(uid, k)]
            thisNVerses = len(nverses[(uid, k)])
            r.append(
                {
                    "item": dict(
                        id=iEncode("n", uid, k),
                        ufname=ufname,
                        ulname=ulname,
                        kw=k,
                        is_published=thisNPub > 0,
                        nnotes=thisNNotes,
                        nverses=thisNVerses,
                    ),
                    "slots": json.dumps([]),
                }
            )
        return r

    def load(self, vr, iid, kw):
        auth = self.auth
        Caching = self.Caching
        Chunk = self.Chunk
        NOTE_DB = self.NOTE_DB

        clauseAtomFirst = Caching.get(
            f"clause_atom_f_{vr}_", lambda: Chunk.getClauseAtomFirstSlot(vr), None
        )
        kwSql = kw.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = "" if myId is None else f""" or created_by = {myId} """
        sql = f"""
select book, clause_atom from note
where keywords like '% {kwSql} %' and version = '{vr}' and (is_shared = 'T' {extra})
;
"""
        clauseAtoms = NOTE_DB.executesql(sql)
        slots = {clauseAtomFirst[x[0]][x[1]] for x in clauseAtoms}
        return normRanges(None, fromset=slots)

    def getInfo(self, iidRep, vr, msgs):
        db = self.db

        (iid, kw) = iDecode("n", iidRep)
        if iid is None:
            return {}
        nRecord = dict(
            id=iidRep, uid=iid, ufname="N?", ulname="N?", kw=kw, versions={}
        )
        nRecord["versions"] = self.countNotes(iid, kw)
        sql = f"""
    select first_name, last_name from auth_user where id = '{iid}'
    ;
    """
        uinfo = db.executesql(sql)
        if uinfo is not None and len(uinfo) > 0:
            nRecord["ufname"] = uinfo[0][0]
            nRecord["ulname"] = uinfo[0][1]
        return nRecord

    def countNotes(self, uid, kw):
        auth = self.auth
        NOTE_DB = self.notedb

        kwSql = kw.replace("'", "''")
        myId = auth.user.id if auth.user is not None else None
        extra = f""" or created_by = {uid} """ if myId == uid else ""
        sql = f"""
select
    version,
    count(id) as amount
from note
where keywords like '% {kwSql} %' and (is_shared = 'T' {extra})
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

        (good, oldNotes, updNotes, newNotes, delNotes) = self.filter(
            myId, notes, clauseAtoms, msgs
        )

        updated = 0
        for nid in updNotes:
            (shared, pub, stat, kw, ntxt) = updNotes[nid]
            (oldShared, oldPub, oldStatus, oldKw, oldTxt) = oldNotes[nid]
            extrafields = []
            if shared and not oldShared:
                extrafields.append(f",\n\tshared_on = '{now}'")
            if not shared and oldShared:
                extrafields.append(",\n\tshared_on = null")
            if pub and not oldPub:
                extrafields.append(f",\n\tpublished_on = '{now}'")
            if not pub and oldPub:
                extrafields.append(",\n\tpublished_on = null")
            shared = "'T'" if shared else "null"
            pub = "'T'" if pub else "null"
            stat = "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat
            updateSql = f"""
update note
    set modified_on = '{now}',
    is_shared = {shared},
    is_published = {pub},
    status = '{stat}',
    keywords = '{kw.replace("'", "''")}',
    ntext = '{ntxt.replace("'", "''")}'{"".join(extrafields)}
where id = {nid}
;
"""
            NOTE_DB.executesql(updateSql)
            updated += 1
        if len(delNotes) > 0:
            deleteSql = f"""
delete from note where id in ({",".join(str(x) for x in delNotes)})
;
"""
            NOTE_DB.executesql(deleteSql)

        for canr in newNotes:
            (shared, pub, stat, kw, ntxt) = newNotes[canr]
            sh = "'T'" if shared else "null"
            sht = f"'{now}'" if shared else "null"
            pb = "'T'" if pub else "null"
            pbt = "'{now}'" if pub else "null"
            fl = "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat
            kwr = kw.replace("'", "''")
            ntr = ntxt.replace("'", "''")
            insertSql = f"""
insert into note
(version, book, chapter, verse, clause_atom,
created_by, created_on, modified_on,
is_shared, shared_on, is_published, published_on,
status, keywords, ntext)
values
('{vr}', '{bk}', {ch}, {vs}, {canr},
 {myId}, '{now}', '{now}', {sh}, {sht}, {pb}, {pbt},
 '{fl}', '{kwr}', '{ntr}')
;
"""
            NOTE_DB.executesql(insertSql)

        changed = False
        if len(delNotes) > 0:
            msgs.append(("special", f"Deleted notes: {len(delNotes)}"))
        if updated > 0:
            msgs.append(("special", f"Updated notes: {updated}"))
        if len(newNotes) > 0:
            msgs.append(("special", f"Added notes: {len(newNotes)}"))
        if len(delNotes) + len(newNotes) + updated == 0:
            msgs.append(("warning", "No changes"))
        else:
            changed = True
            Caching.clear(f"^items_n_{vr}_{bk}_{ch}_")
            if len(newNotes):
                for kw in {newNotes[canr][3] for canr in newNotes}:
                    Caching.clear(
                        f"^verses_{vr}_n_{iEncode('n', myId, kw=kw)}_",
                    )
            if len(delNotes):
                for nid in delNotes:
                    if nid in oldNotes:
                        kw = oldNotes[nid][3]
                        Caching.clear(
                            f"^verses_{vr}_n_{iEncode('n', myId, kw=kw)}_",
                        )
        return changed

    def filter(self, myId, notes, clauseAtoms, msgs):
        NOTE_DB = self.NOTE_DB

        good = True
        otherNotes = set()
        missingNotes = set()
        extraNotes = set()
        sameNotes = set()
        clauseErrors = set()
        emptynew = 0
        oldNotes = {}
        updNotes = {}
        newNotes = {}
        delNotes = set()
        for fields in notes:
            nid = int(fields["nid"])
            uid = int(fields["uid"])
            canr = int(fields["canr"])
            if uid != myId:
                otherNotes.add(nid)
                good = False
                continue
            if canr not in clauseAtoms:
                clauseErrors.add(nid)
                good = False
                continue
            kw = "".join(" " + k + " " for k in fields["kw"].strip().split())
            ntxt = fields["ntxt"].strip()
            if kw == "" and ntxt == "":
                if nid == 0:
                    emptynew += 1
                else:
                    delNotes.add(nid)
                continue
            if nid != 0:
                updNotes[nid] = (
                    fields["shared"],
                    fields["pub"],
                    fields["stat"],
                    kw,
                    ntxt,
                )
            else:
                newNotes[fields["canr"]] = (
                    fields["shared"],
                    fields["pub"],
                    fields["stat"],
                    kw,
                    ntxt,
                )
        if len(updNotes) > 0 or len(delNotes) > 0:
            ids = ",".join(str(x) for x in (set(updNotes.keys()) | delNotes))
            oldSql = f"""
select id, created_by, is_shared, is_published, status, keywords, ntext
from note where id in ({ids})
;
"""
            cresult = NOTE_DB.executesql(oldSql)
            if cresult is not None:
                for (nid, uid, oldShared, oldPub, oldStatus, oldKw, oldTxt) in cresult:
                    remove = False
                    if uid != myId:
                        otherNotes.add(nid)
                        remove = True
                    elif nid not in updNotes and nid not in delNotes:
                        extraNotes.add(nid)
                        remove = True
                    elif nid in updNotes:
                        (shared, pub, stat, kw, ntxt) = updNotes[nid]
                        if not shared:
                            shared = None
                        if not pub:
                            pub = None
                        if (
                            oldStatus == stat
                            and oldKw == kw
                            and oldTxt == ntxt
                            and oldShared == shared
                            and oldPub == pub
                        ):
                            sameNotes.add(nid)
                            if nid not in delNotes:
                                remove = True
                    if remove:
                        if nid in updNotes:
                            del updNotes[nid]
                        if nid in delNotes:
                            delNotes.remove(nid)
                    else:
                        oldNotes[nid] = (oldShared, oldPub, oldStatus, oldKw, oldTxt)
        removable = set()
        for nid in updNotes:
            if nid not in oldNotes:
                if nid not in otherNotes:
                    missingNotes.add(nid)
                    removable.add(nid)
        for nid in removable:
            del updNotes[nid]
        removable = set()
        for nid in delNotes:
            if nid not in oldNotes:
                if nid not in otherNotes:
                    missingNotes.add(nid)
                    removable.add(nid)
        for nid in removable:
            delNotes.remove(nid)
        if len(otherNotes) > 0:
            msgs.append(
                ("error", f"Notes of other users skipped: {len(otherNotes)}")
            )
        if len(missingNotes) > 0:
            msgs.append(("error", f"Non-existing notes: {len(missingNotes)}"))
        if len(extraNotes) > 0:
            msgs.append(("error", f"Notes not shown: {len(extraNotes)}"))
        if len(clauseErrors) > 0:
            msgs.append(
                ("error", f"Notes referring to wrong clause: {len(clauseErrors)}")
            )
        if len(sameNotes) > 0:
            pass
            # msgs.append(('info', f'Unchanged notes: {len(sameNotes)}'))
        if emptynew > 0:
            pass
            # msgs.append(('info', f'Skipped empty new notes: {emptynew}'))
        return (good, oldNotes, updNotes, newNotes, delNotes)

    def upload(self, uid, filetext, now, msgs):
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
                clauseAtom,
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
            if not clauseAtom.isdigit() or int(clauseAtom) > 100000:
                nerrors += 1
                errors.setdefault("unrecognized clause_atom", []).append(
                    f"{i + 1}:{clauseAtom}"
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
                    f"('{version}','{book}',{chapter},{verse},{clauseAtom},"
                    f"'{is_shared}','{is_published}',"
                    f"'{status}','{keywords}','{ntext}',{uid},"
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
and created_by = {uid}
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
    note.created_by as uid,
    shebanq_web.auth_user.first_name as ufname,
    shebanq_web.auth_user.last_name as ulname,
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
                        uid=myId,
                        nid=0,
                        shared=True,
                        pub=False,
                        stat="o",
                        kw="",
                        ntxt="",
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
                nid,
                uid,
                ufname,
                ulname,
                clauseAtom,
                shared,
                pub,
                pubOn,
                status,
                keywords,
                ntext,
            ) in records:
                if (myId is None or (uid != myId) or not edit) and uid not in users:
                    users[uid] = f"{ufname} {ulname}"
                if uid not in clauseAtomUsers[clauseAtom]:
                    clauseAtomUsers[clauseAtom][uid] = None
                pub = pub == "T"
                shared = pub or shared == "T"
                ro = (
                    myId is None
                    or uid != myId
                    or not edit
                    or (pub and pubOn is not None and (pubOn <= now - PUBLISH_FREEZE))
                )
                kws = keywords.strip().split()
                for k in kws:
                    keyIndex[f"{uid} {k}"] = iEncode("n", uid, kw=k)
                notesProto.setdefault(clauseAtom, {}).setdefault(uid, []).append(
                    dict(
                        uid=uid,
                        nid=nid,
                        ro=ro,
                        shared=shared,
                        pub=pub,
                        stat=status,
                        kw=keywords,
                        ntxt=ntext,
                    )
                )
        notes = {}
        for clauseAtom in notesProto:
            for uid in clauseAtomUsers[clauseAtom]:
                notes.setdefault(clauseAtom, []).extend(notesProto[clauseAtom][uid])

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
