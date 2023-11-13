from textwrap import dedent
import collections
import json

from markdown import markdown

from gluon import current

from constants import NULLDT, ALWAYS
from helpers import normRanges, iDecode

from dbconfig import EMDROS_VERSIONS


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
    def __init__(self):
        pass

    def authRead(self, query_id):
        auth = current.auth

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
        auth = current.auth

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

    def page(self, ViewSettings):
        Check = current.Check

        pageConfig = ViewSettings.writeConfig()

        query_id = Check.isId("goto", "q", "query", [])
        if query_id is not None:
            (authorized, msg) = self.authRead(query_id)
            if not authorized:
                query_id = 0
        return dict(
            pageConfig=pageConfig,
            query_id=query_id,
        )

    def body(self):
        """Retrieves a query record based on parameters.
        """
        Check = current.Check
        auth = current.auth

        vr = Check.field("material", "", "version")
        iidRep = Check.field("material", "", "iid")

        (iid, keywords) = iDecode("q", iidRep)
        (authorized, msg) = self.authRead(iid)
        msgs = []
        if authorized and iid == 0:
            msg = f"Not a valid query id: {iidRep}"
        if not authorized or iid == 0:
            msgs.append(("error", msg))
            return dict(
                writable=False,
                iidRep=iidRep,
                vr=vr,
                queryRecord=dict(),
                query=json.dumps(dict()),
                msgs=json.dumps(msgs),
                emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
            )
        queryRecord = self.getInfo(
            auth.user is not None,
            iid,
            vr,
            msgs,
            withIds=True,
            singleVersion=False,
            po=True,
        )
        if queryRecord is None:
            return dict(
                writable=True,
                iidRep=iidRep,
                vr=vr,
                queryRecord=dict(),
                query=json.dumps(dict()),
                msgs=json.dumps(msgs),
                emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
            )

        (authorized, msg) = self.authWrite(iid)

        return dict(
            writable=authorized,
            iidRep=iidRep,
            vr=vr,
            queryRecord=queryRecord,
            query=json.dumps(queryRecord),
            msgs=json.dumps(msgs),
            emdrosVersionsOld=set(EMDROS_VERSIONS[0:-1]),
        )

    def bodyJson(self):
        Check = current.Check

        vr = Check.field("material", "", "version")
        iidRep = Check.field("material", "", "iid")

        (iid, keywords) = iDecode("q", iidRep)
        (authorized, msg) = self.authRead(iid)
        if not authorized:
            result = dict(good=False, msg=[msg], data={})
        else:
            msgs = []
            queryRecord = self.getInfo(
                False, iid, vr, msgs, withIds=False, singleVersion=False, po=True
            )
            result = dict(good=queryRecord is not None, msg=msgs, data=queryRecord)
        return dict(data=json.dumps(result))

    def getItems(self, vr, chapter, onlyPub):
        Caching = current.Caching

        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            ALWAYS,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            ALWAYS,
        )
        chapter_id = chapter.get("id", None)

        if chapter_id is None:
            return []

        slots = collections.defaultdict(lambda: set())
        r = []

        for (query_id, ranges) in queriesFromChapter.get(chapter_id, {}).items():
            if onlyPub and not pubStatus.get(query_id, {}).get(vr, False):
                continue
            for (first_m, last_m) in ranges:
                slots[query_id] |= set(range(first_m, last_m + 1))

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

    def read(self, vr, query_id):
        db = current.db

        query_exe_id = self.getExe(vr, query_id)
        if query_exe_id is None:
            return normRanges([])
        slotSets = db.executesql(
            dedent(
                f"""
                select first_m, last_m
                from monads
                where query_exe_id = {query_exe_id} order by first_m
                ;
                """
            )
        )
        return normRanges(slotSets)

    def getExe(self, vr, query_id):
        db = current.db

        recordsExe = db.executesql(
            dedent(
                f"""
                select id
                from query_exe
                where query_id = {query_id} and version = '{vr}'
                ;
                """
            )
        )
        if recordsExe is None or len(recordsExe) != 1:
            return None
        return recordsExe[0][0]

    def getPlainInfo(self, query_id):
        db = current.db

        records = db.executesql(
            dedent(
                f"""
                select * from query where id = {query_id}
                ;
                """
            ),
            as_dict=True,
        )
        return records[0] if records else {}

    def getBasicInfo(self, vr, query_id):
        db = current.db

        return db.executesql(
            dedent(
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
                """
            ),
            as_dict=True,
        )

    def getTreeInfo(self, query_id):
        db = current.db

        return db.executesql(
            dedent(
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
                """
            ),
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
        """
        If called with `singleVersion` is True,
        we are grabbing queries for the side list of a chapter.
        In this case:
        *   `query_id` is an iterable of query ids
        *   we only want the query exe records of these queries for a single
            version `vr`
        *   we only want query records that are:
            *   belong to a shared query
            *   up to date: executed after modified
        """
        db = current.db

        sqli = (
            dedent(
                """,
                query.created_by as user_id,
                project.id as project_id,
                organization.id as org_id
                """
            )
            if withIds and po
            else ""
        )

        sqlx = (
            dedent(
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
            )
            if singleVersion
            else ""
        )

        sqlp = (
            dedent(
                """,
                project.name as project_name,
                project.website as project_website,
                organization.name as org_name,
                organization.website as org_website
                """
            )
            if po
            else ""
        )

        sqlb = (
            dedent(
                """,
                auth_user.email as uemail
            """
            )
            if showPrivateFields
            else dedent(
                """,
                'n.n@not.disclosed' as uemail
                """
            )
        )

        sqlm = dedent(
            f"""
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
        )

        sqlr = (
            dedent(
                f"""
                inner join query_exe
                on
                    query_exe.query_id = query.id and
                    query_exe.version = '{vr}'
                """
            )
            if singleVersion
            else ""
        )

        sqlpr = (
            dedent(
                """
                inner join organization on query.organization = organization.id
                inner join project on query.project = project.id
                """
            )
            if po
            else ""
        )

        sqlc = (
            dedent(
                f"""
                where query.id in ({",".join(query_id)})
                and query.is_shared = 'T'
                and query_exe.executed_on >= query_exe.modified_on
            """
            )
            if singleVersion
            else dedent(
                f"""
                where query.id = {query_id}
                """
            )
        )

        sqlo = (
            dedent(
                """
                order by auth_user.last_name, query.name
                """
            )
            if singleVersion
            else ""
        )

        sql = dedent(
            f"""
            select{sqlm} from query
            inner join auth_user
            on query.created_by = auth_user.id
            {sqlr}{sqlpr}{sqlc}{sqlo}
            ;
            """
        )
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
            sql = dedent(
                f"""
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
            )
            recordsExe = db.executesql(sql, as_dict=True)
            self.getFields(vr, record, recordsExe, singleVersion=False)
            return record

    def getFields(self, vr, record, recordsExe, singleVersion=False):
        VERSIONS = current.VERSIONS

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
