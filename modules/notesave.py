from textwrap import dedent
import json

from gluon import current

from helpers import iEncode


class NOTESAVE:
    def __init__(self, Note):
        self.Note = Note

    def put(self, myId, vr, bk, ch, vs, notes, clauseAtoms, msgs):
        Caching = current.Caching
        NOTE_DB = current.NOTE_DB

        (good, notesOld, notesUpd, notesNew, notesDel) = self.filter(
            myId, notes, clauseAtoms, msgs
        )

        updated = 0
        doCommit = False
        now = current.request.utcnow

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
            updateSql = dedent(
                f"""
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
            )
            NOTE_DB.executesql(updateSql)
            updated += 1
            doCommit = True

        if len(notesDel) > 0:
            deleteSql = dedent(
                f"""
                delete from note where id in ({",".join(str(x) for x in notesDel)})
                ;
                """
            )
            NOTE_DB.executesql(deleteSql)
            doCommit = True

        for clause_atom in notesNew:
            (is_shared, is_published, status, keywords, ntext) = notesNew[clause_atom]
            sh = "'T'" if is_shared else "null"
            sht = f"'{now}'" if is_shared else "null"
            pb = "'T'" if is_published else "null"
            pbt = f"'{now}'" if is_published else "null"
            fl = "o" if status not in {"o", "*", "+", "?", "-", "!"} else status
            keywordsSql = keywords.replace("'", "''")
            ntr = ntext.replace("'", "''")
            insertSql = dedent(
                f"""
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
            )
            NOTE_DB.executesql(insertSql)
            doCommit = True

        if doCommit:

            NOTE_DB.commit()

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

    def putVerseNotes(self):
        """Save notes.

        Reads request parameters to determine which notes for which verse.
        """
        Check = current.Check
        Note = self.Note
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

        clauseAtoms = Note.getClauseAtoms(vr, bk, ch, vs)
        changed = False

        msgs = []

        if myId is None:
            msgs.append(("error", "You have to be logged in when you save notes"))
        else:
            requestVars = current.request.vars
            notes = (
                json.loads(requestVars.notes)
                if requestVars and requestVars.notes
                else []
            )
            changed = self.put(myId, vr, bk, ch, vs, notes, clauseAtoms, msgs)
        return Note.inVerse(
            vr, bk, ch, vs, myId, clauseAtoms, changed, msgs, authenticated, edit
        )

    def filter(self, myId, notes, clauseAtoms, msgs):
        NOTE_DB = current.NOTE_DB

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
            sqlOld = dedent(
                f"""
                select id, created_by, is_shared, is_published, status, keywords, ntext
                from note where id in ({ids})
                ;
                """
            )
            changeCandidates = NOTE_DB.executesql(sqlOld)
            if changeCandidates is not None:
                for (
                    note_id,
                    user_id,
                    isSharedOld,
                    isPubOld,
                    statusOld,
                    keywordsOld,
                    ntextOld,
                ) in changeCandidates:
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
