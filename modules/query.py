import collections
import json

from markdown import markdown

from constants import NULLDT
from helpers import normRanges


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


def queryStatus(queryExeRecord):
    if not queryExeRecord["executed_on"]:
        return "warning"
    if queryExeRecord["executed_on"] < queryExeRecord["xmodified_on"]:
        return "error"
    return "good"


class QUERY:
    def __init__(self, Check, Caching, auth, db, VERSIONS):
        self.Check = Check
        self.Caching = Caching
        self.auth = auth
        self.db = db
        self.VERSIONS = VERSIONS

    def authRead(self, query_id):
        auth = self.auth

        authorized = None
        if query_id == 0:
            authorized = auth.user is not None
        else:
            record = self.getPlainInfo(query_id)
            if record:
                authorized = record["is_shared"] or (
                    auth.user is not None and record["created_by"] == auth.user.id
                )
        msg = (
            f"No query with id: {query_id}"
            if authorized is None
            else f"You have no access to query with id {query_id}"
        )
        return (authorized, msg)

    def authWrite(self, query_id):
        auth = self.auth

        authorized = None
        if query_id == 0:
            authorized = auth.user is not None
        else:
            record = self.getPlainInfo(query_id)
            if record:
                authorized = (
                    auth.user is not None and record["created_by"] == auth.user.id
                )
        msg = (
            f"No item with id {query_id}"
            if authorized is None
            else f"You have no access to create/modify query with id {query_id}"
        )
        return (authorized, msg)

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

    def read(self, vr, query_id):
        db = self.db

        query_exe_id = self.getExe(vr, query_id)
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

    def getExe(self, vr, query_id):
        db = self.db

        recordsExe = db.executesql(
            f"""
select id from query_exe where query_id = {query_id} and version = '{vr}'
;
"""
        )
        if recordsExe is None or len(recordsExe) != 1:
            return None
        return recordsExe[0][0]

    def getPlainInfo(self, query_id):
        db = self.db

        records = db.executesql(
            f"""
select * from query where id = {query_id}
;
""",
            as_dict=True,
        )
        return records[0] if records else {}

    def getBasicInfo(self, vr, query_id):
        db = self.db

        return db.executesql(
            f"""
select
    query.name as name,
    query.description as description,
    query.is_shared as is_shared,
    query_exe.mql as mql,
    query_exe.is_published as is_published
from query inner join query_exe on
    query.id = query_exe.query_id and query_exe.version = '{vr}'
where query.id = {query_id}
;
""",
            as_dict=True,
        )

    def getTreeInfo(self, query_id):
        db = self.db

        return db.executesql(
            f"""
select
query.id as id,
query.name as name,
organization.id as org_id,
organization.name as org_name,
organization.website as org_website,
project.id as project_id,
project.name as project_name,
project.website as project_website
from query
inner join organization on query.organization = organization.id
inner join project on query.project = project.id
where query.id = {query_id}
;
""",
            as_dict=True,
        )

    def getInfo(
        self,
        showPrivateFields,
        query_id,
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
where query.id in ({",".join(query_id)})
"""
            if singleVersion
            else f"""
where query.id = {query_id}
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
        records = db.executesql(sql, as_dict=True)
        if records is None:
            msgs.append(("error", "Cannot lookup query(ies)"))
            return None
        if singleVersion:
            for record in records:
                self.getFields(vr, record, [], singleVersion=True)
            return records
        else:
            if len(records) == 0:
                msgs.append(("error", f"No query with id {query_id}"))
                return None
            record = records[0]
            record["description_md"] = markdown(
                record["description"] or "", output_format="xhtml5"
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
where query_id = {query_id}
;
"""
            recordsExe = db.executesql(sql, as_dict=True)
            self.getFields(vr, record, recordsExe, singleVersion=False)
            return record

    def getFields(self, vr, record, recordsExe, singleVersion=False):
        VERSIONS = self.VERSIONS

        dateTimeStr(record)
        if not singleVersion:
            record["versions"] = dict(
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
            for recordExe in recordsExe:
                versionExe = recordExe["version"]
                if versionExe not in VERSIONS:
                    continue
                dest = record["versions"][versionExe]
                dest.update(recordExe)
                dest["status"] = queryStatus(dest)
                dateTimeStr(dest)
