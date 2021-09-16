import collections
import json

from markdown import markdown

from constants import NULLDT, PUBLISH_FREEZE, PUBLISH_FREEZE_MSG
from helpers import normalize_ranges, h_esc


RECENT_LIMIT = 50


def datetime_str(fields):
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


def qstatus(qx_record):
    if not qx_record["executed_on"]:
        return "warning"
    if qx_record["executed_on"] < qx_record["xmodified_on"]:
        return "error"
    return "good"


class QUERY:
    def __init__(
        self, Check, Caching, auth, db, versions
    ):
        self.Check = Check
        self.Caching = Caching
        self.auth = auth
        self.db = db
        self.versions = versions

    def dep(self, QueryChapter):
        self.QueryChapter = QueryChapter

    def get_items(self, vr, chapter, onlyPub):
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
        chapterId = chapter.get("id", None)

        if chapterId is None:
            return result

        for (qid, monads) in queriesFromChapter.get(chapterId, {}).items():
            if onlyPub and not pubStatus.get(qid, {}).get(vr, False):
                continue
            for (first_m, last_m) in monads:
                result.append((qid, first_m, last_m))
        return result

    def load(self, vr, iid):
        db = self.db

        xid = self.get_exe(vr, iid)
        if xid is None:
            return normalize_ranges([])
        monad_sets = db.executesql(
            f"""
select first_m, last_m from monads where query_exe_id = {xid} order by first_m
;
"""
        )
        return normalize_ranges(monad_sets)

    def group(self, vr, monadSets):
        monads = collections.defaultdict(lambda: set())
        for (qid, b, e) in monadSets:
            monads[qid] |= set(range(b, e + 1))
        r = []
        if len(monads):
            msgs = []
            queryrecords = self.get_info(
                False,
                (str(q) for q in monads),
                vr,
                msgs,
                with_ids=False,
                single_version=True,
                po=False,
            )
            for q in queryrecords:
                r.append(
                    {"item": q, "monads": json.dumps(sorted(list(monads[q["id"]])))}
                )
        return r

    def get_exe(self, vr, iid):
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

    def get_info(
        self,
        show_private_fields,
        iid,
        vr,
        msgs,
        single_version=False,
        with_ids=True,
        po=False,
    ):
        db = self.db

        sqli = (
            """,
    query.created_by as uid,
    project.id as pid,
    organization.id as oid
"""
            if with_ids and po
            else ""
        )

        sqlx = (
            """,
    query_exe.id as xid,
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
            if single_version
            else ""
        )

        sqlp = (
            """,
    project.name as pname,
    project.website as pwebsite,
    organization.name as oname,
    organization.website as owebsite
"""
            if po
            else ""
        )

        sqlb = (
            """,
    auth_user.email as uemail
"""
            if show_private_fields
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
    auth_user.first_name as ufname,
    auth_user.last_name as ulname
    {sqlb}{sqli}{sqlp}{sqlx}
"""

        sqlr = (
            f"""
inner join query_exe on query_exe.query_id = query.id and query_exe.version = '{vr}'
"""
            if single_version
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
            if single_version
            else f"""
where query.id = {iid}
"""
        )

        sqlo = (
            """
order by auth_user.last_name, query.name
"""
            if single_version
            else ""
        )

        sql = f"""
select{sqlm} from query
inner join auth_user
on query.created_by = auth_user.id
{sqlr}{sqlpr}{sqlc}{sqlo}
;
"""
        records = db.executesql(sql, as_dict=True)
        if records is None:
            msgs.append(("error", "Cannot lookup query(ies)"))
            return None
        if single_version:
            for q_record in records:
                self.fields(vr, q_record, [], single_version=True)
            return records
        else:
            if len(records) == 0:
                msgs.append(("error", f"No query with id {iid}"))
                return None
            q_record = records[0]
            q_record["description_md"] = markdown(
                q_record["description"] or "", output_format="xhtml5"
            )
            sql = f"""
select
    id as xid,
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
            recordx = db.executesql(sql, as_dict=True)
            self.fields(vr, q_record, recordx, single_version=False)
            return q_record

    def fields(self, vr, q_record, recordx, single_version=False):
        versions = self.versions

        datetime_str(q_record)
        if not single_version:
            q_record["versions"] = dict(
                (
                    v,
                    dict(
                        xid=None,
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
                for v in versions
            )
            for rx in recordx:
                vx = rx["version"]
                if vx not in versions:
                    continue
                dest = q_record["versions"][vx]
                dest.update(rx)
                dest["status"] = qstatus(dest)
                datetime_str(dest)

    def store(self, vr, iid, rows, is_shared):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db

        xid = self.get_exe(vr, iid)
        if xid is None:
            return
        db.executesql(
            f"""
delete from monads where query_exe_id={xid}
;
"""
        )
        # Here we clear stuff that will become invalid
        # because of a (re)execution of a query
        # and the deleting of previous results and the storing of new results.
        Caching.clear(f"^verses_{vr}_q_{iid}_")
        Caching.clear(f"^items_q_{vr}_")
        Caching.clear(f"^chart_{vr}_q_{iid}_")
        nrows = len(rows)
        if nrows > 0:
            limit_row = 10000
            start = """
insert into monads (query_exe_id, first_m, last_m) values
"""
            query = ""
            r = 0
            while r < nrows:
                if query != "":
                    db.executesql(query)
                    query = ""
                query += start
                s = min(r + limit_row, len(rows))
                row = rows[r]
                query += f"({xid},{row[0]},{row[1]})"
                if r + 1 < nrows:
                    for row in rows[r + 1:s]:
                        query += f",({xid},{row[0]},{row[1]})"
                r = s
            if query != "":
                db.executesql(query)
                query = ""

        QueryChapter.updateQCindex(vr, iid)

    def upd_shared(self, myid, qid, valsql, now, msgs):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db
        versions = self.versions

        mod_date = None
        mod_date_fld = "shared_on"
        table = "query"
        fname = "is_shared"
        Caching.clear(r"^items_q_")
        fieldval = f" {fname} = '{valsql}'"
        mod_date = now.replace(microsecond=0) if valsql == "T" else None
        mod_date_sql = "null" if mod_date is None else str(mod_date)
        fieldval += f", {mod_date_fld} = {mod_date_sql} "
        sql = f"""
update {table} set{fieldval} where id = {qid}
;
"""
        db.executesql(sql)
        for vr in versions:
            QueryChapter.updateQCindex(vr, qid)
        thismsg = "modified"
        thismsg = "shared" if valsql == "T" else "UNshared"
        msgs.append(("good", thismsg))
        return (mod_date_fld, str(mod_date) if mod_date else NULLDT)

    def upd_published(self, myid, vr, qid, valsql, now, msgs):
        Caching = self.Caching
        QueryChapter = self.QueryChapter
        db = self.db

        mod_date = None
        mod_date_fld = "published_on"
        table = "query_exe"
        fname = "is_published"
        Caching.clear(f"^items_q_{vr}_")
        self.verify_version(qid, vr)
        fieldval = f" {fname} = '{valsql}'"
        mod_date = now.replace(microsecond=0) if valsql == "T" else None
        mod_date_sql = "null" if mod_date is None else str(mod_date)
        fieldval += f", {mod_date_fld} = {mod_date_sql} "
        sql = f"""
update {table} set{fieldval} where query_id = {qid} and version = '{vr}'
;
"""
        db.executesql(sql)
        thismsg = "modified"
        thismsg = "published" if valsql == "T" else "UNpublished"
        QueryChapter.updatePubStatus(vr, qid, valsql == "T")
        msgs.append(("good", thismsg))
        return (mod_date_fld, str(mod_date) if mod_date else NULLDT)

    def upd_field(self, vr, qid, fname, val, now, msgs):
        auth = self.auth
        db = self.db
        Check = self.Check

        good = False
        myid = None
        mod_dates = {}
        mod_cls = {}
        extra = {}
        if auth.user:
            myid = auth.user.id
        for x in [1]:
            valsql = Check.isPublished("q", val, msgs)
            if valsql is None:
                break
            if fname == "is_shared" and valsql == "":
                sql = f"""
select count(*) from query_exe where query_id = {qid} and is_published = 'T'
;
"""
                pv = db.executesql(sql)
                has_public_versions = pv is not None and len(pv) == 1 and pv[0][0] > 0
                if has_public_versions:
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
                mod_cls[
                    "#is_pub_ro"
                ] = f"""fa-{"check" if valsql == "T" else "close"}"""
                mod_cls[f'div[version="{vr}"]'] = (
                    "published" if valsql == "T" else "unpublished"
                )
                extra["execq"] = ("show", valsql != "T")
                if valsql == "T":
                    sql = f"""
select executed_on, modified_on as xmodified_on
from query_exe where query_id = {qid} and version = '{vr}'
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
select is_shared from query where id = {qid}
;
"""
                    pv = db.executesql(sql)
                    is_shared = pv is not None and len(pv) == 1 and pv[0][0] == "T"
                    if not is_shared:
                        (mod_date_fld, mod_date) = self.upd_shared(
                            myid, qid, "T", now, msgs
                        )
                        mod_dates[mod_date_fld] = mod_date
                        extra["is_shared"] = ("checked", True)
                else:
                    sql = f"""
select published_on from query_exe where query_id = {qid} and version = '{vr}'
;
"""
                    pv = db.executesql(sql)
                    pdate_ok = (
                        pv is None
                        or len(pv) != 1
                        or pv[0][0] is None
                        or pv[0][0] > now - PUBLISH_FREEZE
                    )
                    if not pdate_ok:
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
                (mod_date_fld, mod_date) = self.upd_shared(myid, qid, valsql, now, msgs)
            else:
                (mod_date_fld, mod_date) = self.upd_published(
                    myid, vr, qid, valsql, now, msgs
                )
            mod_dates[mod_date_fld] = mod_date
        return (good, mod_dates, mod_cls, extra)

    def verify_version(self, qid, vr):
        db = self.db

        exist_version = db.executesql(
            f"""
select id from query_exe where version = '{vr}' and query_id = {qid}
;
"""
        )
        if exist_version is None or len(exist_version) == 0:
            db.executesql(
                f"""
insert into query_exe (id, version, query_id) values (null, '{vr}', {qid})
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

        pqueryx_sql = f"""
select
    query.id as qid,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    query.name as qname,
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

        pqueryx = db.executesql(pqueryx_sql)
        pqueries = []
        for (qid, ufname, ulname, qname, qexe, qver) in pqueryx:
            text = h_esc(f"{ufname[0]} {ulname[0:9]}: {qname[0:20]}")
            title = h_esc(f"{ufname} {ulname}: {qname}")
            pqueries.append(dict(id=qid, text=text, title=title, version=qver))

        return dict(data=json.dumps(dict(queries=pqueries, msgs=[], good=True)))
