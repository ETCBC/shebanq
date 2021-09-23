from constants import NULLDT, PUBLISH_FREEZE, PUBLISH_FREEZE_MSG
from query import queryStatus


class QUERYSAVE:
    def __init__(self, Check, Caching, Query, auth, db, VERSIONS):
        self.Check = Check
        self.Caching = Caching
        self.Query = Query
        self.auth = auth
        self.db = db
        self.VERSIONS = VERSIONS

    def dep(self, QueryChapter):
        self.QueryChapter = QueryChapter

    def putSlots(self, vr, query_id, rows, is_shared):
        Caching = self.Caching
        Query = self.Query
        QueryChapter = self.QueryChapter
        db = self.db

        query_exe_id = Query.getExe(vr, query_id)
        if query_exe_id is None:
            return
        db.executesql(
            f"""
delete from monads where query_exe_id={query_exe_id}
;
"""
        )
        # Here we clear stuff that will become invalid
        # because of a (re)execution of a query
        # and the deleting of previous results and the storing of new results.
        Caching.clear(f"^verses_{vr}_q_{query_id}_")
        Caching.clear(f"^items_q_{vr}_")
        Caching.clear(f"^chart_{vr}_q_{query_id}_")
        nRows = len(rows)
        if nRows > 0:
            limitRow = 10000
            start = """
insert into monads (query_exe_id, first_m, last_m) values
"""
            query = ""
            r = 0
            while r < nRows:
                if query != "":
                    db.executesql(query)
                    query = ""
                query += start
                s = min(r + limitRow, len(rows))
                row = rows[r]
                query += f"({query_exe_id},{row[0]},{row[1]})"
                if r + 1 < nRows:
                    for row in rows[r + 1:s]:
                        query += f",({query_exe_id},{row[0]},{row[1]})"
                r = s
            if query != "":
                db.executesql(query)
                query = ""

        QueryChapter.updateQCindex(vr, query_id)

    def putSharing(self, vr, query_id, fname, val, now, msgs):
        auth = self.auth
        db = self.db
        Check = self.Check

        good = False
        myId = None
        modDates = {}
        modCls = {}
        extra = {}
        if auth.user:
            myId = auth.user.id
        for x in [1]:
            valsql = Check.isPublished("q", val, msgs)
            if valsql is None:
                break
            if fname == "is_shared" and valsql == "":
                sql = f"""
select count(*) from query_exe where query_id = {query_id} and is_published = 'T'
;
"""
                pv = db.executesql(sql)
                hasPublicVersions = pv is not None and len(pv) == 1 and pv[0][0] > 0
                if hasPublicVersions:
                    msgs.append(
                        (
                            "error",
                            (
                                "You cannot UNshare this query because there is"
                                "a published execution record"
                            ),
                        )
                    )
                    break
            if fname == "is_published":
                modCls["#is_pub_ro"] = f"""fa-{"check" if valsql == "T" else "close"}"""
                modCls[f'div[version="{vr}"]'] = (
                    "published" if valsql == "T" else "unpublished"
                )
                extra["execq"] = ("show", valsql != "T")
                if valsql == "T":
                    sql = f"""
select executed_on, modified_on as xmodified_on
from query_exe where query_id = {query_id} and version = '{vr}'
;
"""
                    pv = db.executesql(sql, as_dict=True)
                    if pv is None or len(pv) != 1:
                        msgs.append(
                            (
                                "error",
                                "cannot determine whether query results are up to date",
                            )
                        )
                        break
                    uptodate = queryStatus(pv[0])
                    if uptodate != "good":
                        msgs.append(
                            (
                                "error",
                                (
                                    "You can only publish "
                                    "if the query results are up to date"
                                ),
                            )
                        )
                        break
                    sql = f"""
select is_shared from query where id = {query_id}
;
"""
                    pv = db.executesql(sql)
                    is_shared = pv is not None and len(pv) == 1 and pv[0][0] == "T"
                    if not is_shared:
                        (modDateFld, modDate) = self.putShared(
                            myId, query_id, "T", now, msgs
                        )
                        modDates[modDateFld] = modDate
                        extra["is_shared"] = ("checked", True)
                else:
                    sql = f"""
select published_on from query_exe where query_id = {query_id} and version = '{vr}'
;
"""
                    pv = db.executesql(sql)
                    pubDateOk = (
                        pv is None
                        or len(pv) != 1
                        or pv[0][0] is None
                        or pv[0][0] > now - PUBLISH_FREEZE
                    )
                    if not pubDateOk:
                        msgs.append(
                            (
                                "error",
                                (
                                    "You cannot UNpublish this query because"
                                    "it has been published more than "
                                    f"{PUBLISH_FREEZE_MSG} ago"
                                ),
                            )
                        )
                        break

            good = True

        if good:
            if fname == "is_shared":
                (modDateFld, modDate) = self.putShared(
                    myId, query_id, valsql, now, msgs
                )
            else:
                (modDateFld, modDate) = self.putPublished(
                    myId, vr, query_id, valsql, now, msgs
                )
            modDates[modDateFld] = modDate
        return (good, modDates, modCls, extra)

    def putShared(self, myId, query_id, valsql, now, msgs):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db
        VERSIONS = self.VERSIONS

        modDate = None
        modDateFld = "shared_on"
        table = "query"
        fname = "is_shared"
        Caching.clear(r"^items_q_")
        fieldval = f" {fname} = '{valsql}'"
        modDate = now.replace(microsecond=0) if valsql == "T" else None
        modDateSql = "null" if modDate is None else str(modDate)
        fieldval += f", {modDateFld} = {modDateSql} "
        sql = f"""
update {table} set{fieldval} where id = {query_id}
;
"""
        db.executesql(sql)
        for vr in VERSIONS:
            QueryChapter.updateQCindex(vr, query_id)
        thismsg = "modified"
        thismsg = "shared" if valsql == "T" else "UNshared"
        msgs.append(("good", thismsg))
        return (modDateFld, str(modDate) if modDate else NULLDT)

    def putPublished(self, myId, vr, query_id, valsql, now, msgs):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db

        modDate = None
        modDateFld = "published_on"
        table = "query_exe"
        fname = "is_published"
        Caching.clear(f"^items_q_{vr}_")
        self.verifyVersion(vr, query_id)
        fieldval = f" {fname} = '{valsql}'"
        modDate = now.replace(microsecond=0) if valsql == "T" else None
        modDateSql = "null" if modDate is None else str(modDate)
        fieldval += f", {modDateFld} = {modDateSql} "
        sql = f"""
update {table} set{fieldval} where query_id = {query_id} and version = '{vr}'
;
"""
        db.executesql(sql)
        thismsg = "modified"
        thismsg = "published" if valsql == "T" else "UNpublished"
        QueryChapter.updatePubStatus(vr, query_id, valsql == "T")
        msgs.append(("good", thismsg))
        return (modDateFld, str(modDate) if modDate else NULLDT)

    def putMeta(self, vr, query_id, fields, fieldsExe):
        Caching = self.Caching
        db = self.db

        if len(fields):
            fieldRep = ", ".join(
                f" {f} = '{fields[f]}'" for f in fields if f != "status"
            )
            sql = f"""
update query set{fieldRep} where id = {query_id}
;
"""
            db.executesql(sql)
            Caching.clear(r"^items_q_")
        if len(fieldsExe):
            fieldRep = ", ".join(
                f" {f} = '{fieldsExe[f]}'" for f in fieldsExe if f != "status"
            )
            sql = f"""
update query_exe set{fieldRep} where query_id = {query_id} and version = '{vr}'
;
"""
            db.executesql(sql)
            Caching.clear(f"^items_q_{vr}_")

    def verifyVersion(self, vr, query_id):
        db = self.db

        existVersion = db.executesql(
            f"""
select id from query_exe where version = '{vr}' and query_id = {query_id}
;
"""
        )
        if existVersion is None or len(existVersion) == 0:
            db.executesql(
                f"""
insert into query_exe (id, version, query_id) values (null, '{vr}', {query_id})
;
"""
            )
