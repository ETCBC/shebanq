import collections
import json

from markdown import markdown

from constants import NULLDT, PUBLISH_FREEZE, PUBLISH_FREEZE_MSG
from helpers import normRanges, hEsc


RECENT_LIMIT = 50


def dateTimeStr(fields):
    for f in (
        "created_on",
        "modified_on",
        "shared_on",
        "xmodified_on",
        "executed_on",
        "published_on",
    ):
        if f in fields:
            ov = fields[f]
            fields[f] = str(ov) if ov else NULLDT
    for f in ("is_shared", "is_published"):
        if f in fields:
            fields[f] = fields[f] == "T"


def qstatus(qxRecord):
    if not qxRecord["executed_on"]:
        return "warning"
    if qxRecord["executed_on"] < qxRecord["xmodified_on"]:
        return "error"
    return "good"


class QUERY:
    def __init__(self, Check, Caching, auth, db, VERSIONS):
        self.Check = Check
        self.Caching = Caching
        self.auth = auth
        self.db = db
        self.VERSIONS = VERSIONS

    def dep(self, QueryChapter):
        self.QueryChapter = QueryChapter

    def getItems(self, vr, chapter, onlyPub):
        Caching = self.Caching

        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            None,
        )
        result = []
        chapter_id = chapter.get("id", None)

        if chapter_id is None:
            return result

        for (query_id, slots) in queriesFromChapter.get(chapter_id, {}).items():
            if onlyPub and not pubStatus.get(query_id, {}).get(vr, False):
                continue
            for (first_m, last_m) in slots:
                result.append((query_id, first_m, last_m))
        return result

    def load(self, vr, iid):
        db = self.db

        query_exe_id = self.getExe(vr, iid)
        if query_exe_id is None:
            return normRanges([])
        slotSets = db.executesql(
            f"""
select first_m, last_m from monads where query_exe_id = {query_exe_id} order by first_m
;
"""
        )
        return normRanges(slotSets)

    def group(self, vr, slotSets):
        slots = collections.defaultdict(lambda: set())
        for (query_id, b, e) in slotSets:
            slots[query_id] |= set(range(b, e + 1))
        r = []
        if len(slots):
            msgs = []
            queryrecords = self.getInfo(
                False,
                (str(q) for q in slots),
                vr,
                msgs,
                withIds=False,
                singleVersion=True,
                po=False,
            )
            for q in queryrecords:
                r.append({"item": q, "slots": json.dumps(sorted(list(slots[q["id"]])))})
        return r

    def getExe(self, vr, iid):
        db = self.db

        recordx = db.executesql(
            f"""
select id from query_exe where query_id = {iid} and version = '{vr}'
;
"""
        )
        if recordx is None or len(recordx) != 1:
            return None
        return recordx[0][0]

    def getInfo(
        self,
        showPrivateFields,
        iid,
        vr,
        msgs,
        singleVersion=False,
        withIds=True,
        po=False,
    ):
        db = self.db

        sqli = (
            """,
    query.created_by as user_id,
    project.id as project_id,
    organization.id as org_id
"""
            if withIds and po
            else ""
        )

        sqlx = (
            """,
    query_exe.id as query_exe_id,
    query_exe.mql as mql,
    query_exe.version as version,
    query_exe.eversion as eversion,
    query_exe.resultmonads as resultmonads,
    query_exe.results as results,
    query_exe.executed_on as executed_on,
    query_exe.modified_on as xmodified_on,
    query_exe.is_published as is_published,
    query_exe.published_on as published_on
"""
            if singleVersion
            else ""
        )

        sqlp = (
            """,
    project.name as project_name,
    project.website as project_website,
    organization.name as org_name,
    organization.website as org_website
"""
            if po
            else ""
        )

        sqlb = (
            """,
    auth_user.email as uemail
"""
            if showPrivateFields
            else """,
        'n.n@not.disclosed' as uemail
    """
        )

        sqlm = f"""
    query.id as id,
    query.name as name,
    query.description as description,
    query.created_on as created_on,
    query.modified_on as modified_on,
    query.is_shared as is_shared,
    query.shared_on as shared_on,
    auth_user.first_name,
    auth_user.last_name
    {sqlb}{sqli}{sqlp}{sqlx}
"""

        sqlr = (
            f"""
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{vr}'
"""
            if singleVersion
            else ""
        )

        sqlpr = (
            """
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
"""
            if po
            else ""
        )

        sqlc = (
            f"""
where query.id in ({",".join(iid)})
"""
            if singleVersion
            else f"""
where query.id = {iid}
"""
        )

        sqlo = (
            """
order by auth_user.last_name, query.name
"""
            if singleVersion
            else ""
        )

        sql = f"""
select{sqlm} from query
inner join auth_user
on query.created_by = auth_user.id
{sqlr}{sqlpr}{sqlc}{sqlo}
;
"""
        records = db.executesql(sql, asDict=True)
        if records is None:
            msgs.append(("error", "Cannot lookup query(ies)"))
            return None
        if singleVersion:
            for queryRecord in records:
                self.fields(vr, queryRecord, [], singleVersion=True)
            return records
        else:
            if len(records) == 0:
                msgs.append(("error", f"No query with id {iid}"))
                return None
            queryRecord = records[0]
            queryRecord["description_md"] = markdown(
                queryRecord["description"] or "", output_format="xhtml5"
            )
            sql = f"""
select
    id as query_exe_id,
    mql,
    version,
    eversion,
    resultmonads,
    results,
    executed_on,
    modified_on as xmodified_on,
    is_published,
    published_on
from query_exe
where query_id = {iid}
;
"""
            recordx = db.executesql(sql, asDict=True)
            self.fields(vr, queryRecord, recordx, singleVersion=False)
            return queryRecord

    def fields(self, vr, queryRecord, recordx, singleVersion=False):
        VERSIONS = self.VERSIONS

        dateTimeStr(queryRecord)
        if not singleVersion:
            queryRecord["versions"] = dict(
                (
                    v,
                    dict(
                        query_exe_id=None,
                        mql=None,
                        status="warning",
                        is_published=None,
                        results=None,
                        resultmonads=None,
                        xmodified_on=None,
                        executed_on=None,
                        eversion=None,
                        published_on=None,
                    ),
                )
                for v in VERSIONS
            )
            for rx in recordx:
                vx = rx["version"]
                if vx not in VERSIONS:
                    continue
                dest = queryRecord["versions"][vx]
                dest.update(rx)
                dest["status"] = qstatus(dest)
                dateTimeStr(dest)

    def store(self, vr, iid, rows, is_shared):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db

        query_exe_id = self.getExe(vr, iid)
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
        Caching.clear(f"^verses_{vr}_q_{iid}_")
        Caching.clear(f"^items_q_{vr}_")
        Caching.clear(f"^chart_{vr}_q_{iid}_")
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

        QueryChapter.updateQCindex(vr, iid)

    def updShared(self, myId, query_id, valsql, now, msgs):
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

    def updPublished(self, myId, vr, query_id, valsql, now, msgs):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db

        modDate = None
        modDateFld = "published_on"
        table = "query_exe"
        fname = "is_published"
        Caching.clear(f"^items_q_{vr}_")
        self.verifyVersion(query_id, vr)
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

    def updField(self, vr, query_id, fname, val, now, msgs):
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
                    pv = db.executesql(sql, asDict=True)
                    if pv is None or len(pv) != 1:
                        msgs.append(
                            (
                                "error",
                                "cannot determine whether query results are up to date",
                            )
                        )
                        break
                    uptodate = qstatus(pv[0])
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
                        (modDateFld, modDate) = self.updShared(
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
                (modDateFld, modDate) = self.updShared(
                    myId, query_id, valsql, now, msgs
                )
            else:
                (modDateFld, modDate) = self.updPublished(
                    myId, vr, query_id, valsql, now, msgs
                )
            modDates[modDateFld] = modDate
        return (good, modDates, modCls, extra)

    def verifyVersion(self, query_id, vr):
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

    def recent(self):
        # The next query contains a clever idea from
        # http://stackoverflow.com/a/5657514
        # (http://stackoverflow.com/questions/5657446/mysql-query-max-group-by)
        # We want to find the most recent mql queries.
        # Queries may have multiple executions.
        # We want to have the queries with the most recent executions.
        # From such queries, we only want to have that one most recent executions.
        # This idea can be obtained by left outer joining the query_exe table
        # with itself (qe1 with qe2) # on the condition that the rows are combined
        # where qe1 and qe2 belong to the same query, and qe2 is more recent.
        # Rows in the combined table where qe2 is null,
        # are such that qe1 is most recent.
        # This is the basic idea.
        # We then have to refine it: we only want shared queries.
        # That is an easy where condition on the final result.
        # We only want to have up-to-date queries.
        # So the join condition is not that qe2 is more recent,
        # but that qe2 is up-to-date and more recent.
        # And we need to add a where to express that qe1 is up to date.

        db = self.db

        projectQueryXSql = f"""
select
    query.id as query_id,
    auth_user.first_name,
    auth_user.last_name,
    query.name as query_name,
    qe.executed_on as qexe,
    qe.version as qver
from query inner join
    (
        select qe1.query_id, qe1.executed_on, qe1.version
        from query_exe qe1
          left outer join query_exe qe2
            on (
                qe1.query_id = qe2.query_id and
                qe1.executed_on < qe2.executed_on and
                qe2.executed_on >= qe2.modified_on
            )
        where
            (qe1.executed_on is not null and qe1.executed_on >= qe1.modified_on) and
            qe2.query_id is null
    ) as qe
on qe.query_id = query.id
inner join auth_user on query.created_by = auth_user.id
where query.is_shared = 'T'
order by qe.executed_on desc, auth_user.last_name
limit {RECENT_LIMIT};
"""

        pqueryx = db.executesql(projectQueryXSql)
        pqueries = []
        for (query_id, first_name, last_name, query_name, qexe, qver) in pqueryx:
            text = hEsc(f"{first_name[0]} {last_name[0:9]}: {query_name[0:20]}")
            title = hEsc(f"{first_name} {last_name}: {query_name}")
            pqueries.append(dict(id=query_id, text=text, title=title, version=qver))

        return dict(data=json.dumps(dict(queries=pqueries, msgs=[], good=True)))

    def feed(self):
        db = self.db

        sql = """
    select
        query.id as query_id,
        auth_user.first_name,
        auth_user.last_name,
        query.name as query_name,
        query.description,
        qe.id as qvid,
        qe.executed_on as qexe,
        qe.version as qver
    from query inner join
        (
            select t1.id, t1.query_id, t1.executed_on, t1.version
            from query_exe t1
              left outer join query_exe t2
                on (
                    t1.query_id = t2.query_id and
                    t1.executed_on < t2.executed_on and
                    t2.executed_on >= t2.modified_on
                )
            where
                (t1.executed_on is not null and t1.executed_on >= t1.modified_on) and
                t2.query_id is null
        ) as qe
    on qe.query_id = query.id
    inner join auth_user on query.created_by = auth_user.id
    where query.is_shared = 'T'
    order by qe.executed_on desc, auth_user.last_name
    """

        return db.executesql(sql)
