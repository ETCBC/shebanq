import collections
import json

from constants import PUBLISH_FREEZE
from helpers import (
    iid_encode,
    iid_decode,
    normalize_ranges,
    nt_statclass,
)


class NOTE:
    def __init__(
        self,
        Caching,
        Chunk,
        auth,
        db,
        note_db,
        passage_dbs,
        versions,
    ):
        self.Caching = Caching
        self.auth = auth
        self.db = db
        self.note_db = note_db
        self.passage_dbs = passage_dbs
        self.versions = versions

    def get_items(self, vr, book, chapter, pub):
        note_db = self.note_db

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
        records = note_db.executesql(sql)
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
            this_npub = npub[(uid, k)]
            this_nnotes = nnotes[(uid, k)]
            this_nverses = len(nverses[(uid, k)])
            r.append(
                {
                    "item": dict(
                        id=iid_encode("n", uid, k),
                        ufname=ufname,
                        ulname=ulname,
                        kw=k,
                        is_published=this_npub > 0,
                        nnotes=this_nnotes,
                        nverses=this_nverses,
                    ),
                    "monads": json.dumps([]),
                }
            )
        return r

    def load(self, vr, iid, kw):
        auth = self.auth
        Caching = self.Caching
        Chunk = self.Chunk
        note_db = self.note_db

        clause_atom_first = Caching.get(
            f"clause_atom_f_{vr}_", lambda: Chunk.get_clause_atom_fmonad(vr), None
        )
        kw_sql = kw.replace("'", "''")
        myid = auth.user.id if auth.user is not None else None
        extra = "" if myid is None else f""" or created_by = {myid} """
        sql = f"""
select book, clause_atom from note
where keywords like '% {kw_sql} %' and version = '{vr}' and (is_shared = 'T' {extra})
;
"""
        clause_atoms = note_db.executesql(sql)
        monads = {clause_atom_first[x[0]][x[1]] for x in clause_atoms}
        return normalize_ranges(None, fromset=monads)

    def get_info(self, iidrep, vr, msgs):
        db = self.db

        (iid, kw) = iid_decode("n", iidrep)
        if iid is None:
            return {}
        n_record = dict(
            id=iidrep, uid=iid, ufname="N?", ulname="N?", kw=kw, versions={}
        )
        n_record["versions"] = self.count_n_notes(iid, kw)
        sql = f"""
    select first_name, last_name from auth_user where id = '{iid}'
    ;
    """
        uinfo = db.executesql(sql)
        if uinfo is not None and len(uinfo) > 0:
            n_record["ufname"] = uinfo[0][0]
            n_record["ulname"] = uinfo[0][1]
        return n_record

    def count_n_notes(self, uid, kw):
        auth = self.auth
        note_db = self.notedb

        kw_sql = kw.replace("'", "''")
        myid = auth.user.id if auth.user is not None else None
        extra = f""" or created_by = {uid} """ if myid == uid else ""
        sql = f"""
select
    version,
    count(id) as amount
from note
where keywords like '% {kw_sql} %' and (is_shared = 'T' {extra})
group by version
;"""
        records = note_db.executesql(sql)
        vrs = set()
        versions_info = {}
        for (vr, amount) in records:
            vrs.add(vr)
            versions_info[vr] = dict(n=amount)
        return versions_info

    def save(self, myid, vr, bk, ch, vs, now, notes, clause_atoms, msgs):
        Caching = self.Caching
        note_db = self.note_db

        (good, old_notes, upd_notes, new_notes, del_notes) = self.filter(
            myid, notes, clause_atoms, msgs
        )

        updated = 0
        for nid in upd_notes:
            (shared, pub, stat, kw, ntxt) = upd_notes[nid]
            (o_shared, o_pub, o_stat, o_kw, o_ntxt) = old_notes[nid]
            extrafields = []
            if shared and not o_shared:
                extrafields.append(f",\n\tshared_on = '{now}'")
            if not shared and o_shared:
                extrafields.append(",\n\tshared_on = null")
            if pub and not o_pub:
                extrafields.append(f",\n\tpublished_on = '{now}'")
            if not pub and o_pub:
                extrafields.append(",\n\tpublished_on = null")
            shared = "'T'" if shared else "null"
            pub = "'T'" if pub else "null"
            stat = "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat
            update_sql = f"""
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
            note_db.executesql(update_sql)
            updated += 1
        if len(del_notes) > 0:
            del_sql = f"""
delete from note where id in ({",".join(str(x) for x in del_notes)})
;
"""
            note_db.executesql(del_sql)

        for canr in new_notes:
            (shared, pub, stat, kw, ntxt) = new_notes[canr]
            sh = "'T'" if shared else "null"
            sht = f"'{now}'" if shared else "null"
            pb = "'T'" if pub else "null"
            pbt = "'{now}'" if pub else "null"
            fl = "o" if stat not in {"o", "*", "+", "?", "-", "!"} else stat
            kwr = kw.replace("'", "''")
            ntr = ntxt.replace("'", "''")
            insert_sql = f"""
insert into note
(version, book, chapter, verse, clause_atom,
created_by, created_on, modified_on,
is_shared, shared_on, is_published, published_on,
status, keywords, ntext)
values
('{vr}', '{bk}', {ch}, {vs}, {canr},
 {myid}, '{now}', '{now}', {sh}, {sht}, {pb}, {pbt},
 '{fl}', '{kwr}', '{ntr}')
;
"""
            note_db.executesql(insert_sql)

        changed = False
        if len(del_notes) > 0:
            msgs.append(("special", f"Deleted notes: {len(del_notes)}"))
        if updated > 0:
            msgs.append(("special", f"Updated notes: {updated}"))
        if len(new_notes) > 0:
            msgs.append(("special", f"Added notes: {len(new_notes)}"))
        if len(del_notes) + len(new_notes) + updated == 0:
            msgs.append(("warning", "No changes"))
        else:
            changed = True
            Caching.clear(f"^items_n_{vr}_{bk}_{ch}_")
            if len(new_notes):
                for kw in {new_notes[canr][3] for canr in new_notes}:
                    Caching.clear(
                        f"^verses_{vr}_n_{iid_encode('n', myid, kw=kw)}_",
                    )
            if len(del_notes):
                for nid in del_notes:
                    if nid in old_notes:
                        kw = old_notes[nid][3]
                        Caching.clear(
                            f"^verses_{vr}_n_{iid_encode('n', myid, kw=kw)}_",
                        )
        return changed

    def filter(self, myid, notes, these_clause_atoms, msgs):
        note_db = self.note_db

        good = True
        other_user_notes = set()
        missing_notes = set()
        extra_notes = set()
        same_notes = set()
        clause_errors = set()
        emptynew = 0
        old_notes = {}
        upd_notes = {}
        new_notes = {}
        del_notes = set()
        for fields in notes:
            nid = int(fields["nid"])
            uid = int(fields["uid"])
            canr = int(fields["canr"])
            if uid != myid:
                other_user_notes.add(nid)
                good = False
                continue
            if canr not in these_clause_atoms:
                clause_errors.add(nid)
                good = False
                continue
            kw = "".join(" " + k + " " for k in fields["kw"].strip().split())
            ntxt = fields["ntxt"].strip()
            if kw == "" and ntxt == "":
                if nid == 0:
                    emptynew += 1
                else:
                    del_notes.add(nid)
                continue
            if nid != 0:
                upd_notes[nid] = (
                    fields["shared"],
                    fields["pub"],
                    fields["stat"],
                    kw,
                    ntxt,
                )
            else:
                new_notes[fields["canr"]] = (
                    fields["shared"],
                    fields["pub"],
                    fields["stat"],
                    kw,
                    ntxt,
                )
        if len(upd_notes) > 0 or len(del_notes) > 0:
            ids = ",".join(str(x) for x in (set(upd_notes.keys()) | del_notes))
            old_sql = f"""
select id, created_by, is_shared, is_published, status, keywords, ntext
from note where id in ({ids})
;
"""
            cresult = note_db.executesql(old_sql)
            if cresult is not None:
                for (nid, uid, o_shared, o_pub, o_stat, o_kw, o_ntxt) in cresult:
                    remove = False
                    if uid != myid:
                        other_user_notes.add(nid)
                        remove = True
                    elif nid not in upd_notes and nid not in del_notes:
                        extra_notes.add(nid)
                        remove = True
                    elif nid in upd_notes:
                        (shared, pub, stat, kw, ntxt) = upd_notes[nid]
                        if not shared:
                            shared = None
                        if not pub:
                            pub = None
                        if (
                            o_stat == stat
                            and o_kw == kw
                            and o_ntxt == ntxt
                            and o_shared == shared
                            and o_pub == pub
                        ):
                            same_notes.add(nid)
                            if nid not in del_notes:
                                remove = True
                    if remove:
                        if nid in upd_notes:
                            del upd_notes[nid]
                        if nid in del_notes:
                            del_notes.remove(nid)
                    else:
                        old_notes[nid] = (o_shared, o_pub, o_stat, o_kw, o_ntxt)
        to_remove = set()
        for nid in upd_notes:
            if nid not in old_notes:
                if nid not in other_user_notes:
                    missing_notes.add(nid)
                    to_remove.add(nid)
        for nid in to_remove:
            del upd_notes[nid]
        to_remove = set()
        for nid in del_notes:
            if nid not in old_notes:
                if nid not in other_user_notes:
                    missing_notes.add(nid)
                    to_remove.add(nid)
        for nid in to_remove:
            del_notes.remove(nid)
        if len(other_user_notes) > 0:
            msgs.append(
                ("error", f"Notes of other users skipped: {len(other_user_notes)}")
            )
        if len(missing_notes) > 0:
            msgs.append(("error", f"Non-existing notes: {len(missing_notes)}"))
        if len(extra_notes) > 0:
            msgs.append(("error", f"Notes not shown: {len(extra_notes)}"))
        if len(clause_errors) > 0:
            msgs.append(
                ("error", f"Notes referring to wrong clause: {len(clause_errors)}")
            )
        if len(same_notes) > 0:
            pass
            # msgs.append(('info', f'Unchanged notes: {len(same_notes)}'))
        if emptynew > 0:
            pass
            # msgs.append(('info', f'Skipped empty new notes: {emptynew}'))
        return (good, old_notes, upd_notes, new_notes, del_notes)

    def upload(self, uid, filetext, now, msgs):
        Caching = self.Caching
        Chunk = self.Chunk
        note_db = self.note_db
        versions = self.versions

        my_versions = set()
        book_info = {}
        for vr in versions:
            my_versions.add(vr)
            book_info[vr] = Chunk.get_books(vr)[0]
        normative_fields = "\t".join(
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
        fieldnames = normative_fields.split("\t")
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
        this_chunk = []
        this_i = 0
        for (i, linenl) in enumerate(filetext.value.decode("utf8").split("\n")):
            line = linenl.rstrip()
            if line == "":
                continue
            if i == 0:
                if line != normative_fields:
                    msgs.append(
                        [
                            "error",
                            (
                                f"Wrong fields: {line}. "
                                f"Required fields are {normative_fields}"
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
            if version not in my_versions:
                nerrors += 1
                errors.setdefault("unrecognized version", []).append(
                    f"{i + 1}:{version}"
                )
                continue
            books = book_info[version]
            if book not in books:
                nerrors += 1
                errors.setdefault("unrecognized book", []).append(f"{i + 1}:{book}")
                continue
            max_chapter = books[book]
            if not chapter.isdigit() or int(chapter) > max_chapter:
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
            if status not in nt_statclass:
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
            this_chunk.append(
                (
                    f"('{version}','{book}',{chapter},{verse},{clause_atom},"
                    f"'{is_shared}','{is_published}',"
                    f"'{status}','{keywords}','{ntext}',{uid},"
                    f"'{created_on}','{modified_on}',{shared_on},{published_on},'b')"
                )
            )
            this_i += 1
            if this_i >= chunksize:
                chunks.append(this_chunk)
                this_chunk = []
                this_i = 0
        if len(this_chunk):
            chunks.append(this_chunk)

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
            note_db.executesql(delSql)
            for chunk in chunks:
                chunkRep = ",\n".join(chunk)
                sql = f"{sqlhead} {chunkRep};"
                note_db.executesql(sql)
            Caching.clear(r"^items_n_")
            for vr in my_versions:
                Caching.clear(f"^verses_{vr}_n_")
        for msg in sorted(errors):
            istr = ",".join(str(i) for i in errors[msg])
            msgs.append(["error", f"{msg}: {istr}"])
        msgs.append(["good" if good else "error", "Done"])
        return True

    def inChapter(
        self, vr, bk, ch, vs, myid, clause_atoms, changed, now, msgs, logged_in, edit
    ):
        note_db = self.note_db

        condition = """note.is_shared = 'T' or note.is_published = 'T' """
        if myid is not None:
            condition += f""" or note.created_by = {myid} """

        note_sql = f"""
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

        records = note_db.executesql(note_sql)
        users = {}
        nkey_index = {}
        notes_proto = collections.defaultdict(lambda: {})
        ca_users = collections.defaultdict(lambda: collections.OrderedDict())
        if myid is not None and edit:
            users[myid] = "me"
            for ca in clause_atoms:
                notes_proto[ca][myid] = [
                    dict(
                        uid=myid,
                        nid=0,
                        shared=True,
                        pub=False,
                        stat="o",
                        kw="",
                        ntxt="",
                    )
                ]
                ca_users[ca][myid] = None
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
                ca,
                shared,
                pub,
                pub_on,
                status,
                keywords,
                ntext,
            ) in records:
                if (myid is None or (uid != myid) or not edit) and uid not in users:
                    users[uid] = f"{ufname} {ulname}"
                if uid not in ca_users[ca]:
                    ca_users[ca][uid] = None
                pub = pub == "T"
                shared = pub or shared == "T"
                ro = (
                    myid is None
                    or uid != myid
                    or not edit
                    or (pub and pub_on is not None and (pub_on <= now - PUBLISH_FREEZE))
                )
                kws = keywords.strip().split()
                for k in kws:
                    nkey_index[f"{uid} {k}"] = iid_encode("n", uid, kw=k)
                notes_proto.setdefault(ca, {}).setdefault(uid, []).append(
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
        for ca in notes_proto:
            for uid in ca_users[ca]:
                notes.setdefault(ca, []).extend(notes_proto[ca][uid])

        return json.dumps(
            dict(
                good=good,
                changed=changed,
                msgs=msgs,
                users=users,
                notes=notes,
                nkey_index=nkey_index,
                logged_in=logged_in,
            )
        )
