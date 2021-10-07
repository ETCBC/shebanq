from textwrap import dedent
import json

from gluon import current

from constants import NULLDT, PUBLISH_FREEZE, PUBLISH_FREEZE_MSG
from dbconfig import EMDROS_VERSIONS
from query import queryStatus
from helpers import countSlots
from mql import mql


class QUERYSAVE:
    def __init__(self, Query, QueryChapter):
        self.Query = Query
        self.QueryChapter = QueryChapter

    def putSlots(self, vr, query_id, rows):
        Caching = current.Caching
        Query = self.Query
        QueryChapter = self.QueryChapter
        db = current.db

        query_exe_id = Query.getExe(vr, query_id)
        if query_exe_id is None:
            return

        db.executesql(
            dedent(
                f"""
                delete from monads where query_exe_id={query_exe_id}
                ;
                """
            )
        )

        db.commit()

        # Here we clear stuff that will become invalid
        # because of a (re)execution of a query
        # and the deleting of previous results and the storing of new results.
        Caching.clear(f"^verses_{vr}_q_{query_id}_")
        Caching.clear(f"^items_q_{vr}_")
        Caching.clear(f"^chart_{vr}_q_{query_id}_")
        nRows = len(rows)
        if nRows > 0:
            limitRow = 10000
            start = dedent(
                """
                insert into monads (query_exe_id, first_m, last_m) values
                """
            )
            query = ""
            r = 0
            while r < nRows:
                if query != "":
                    db.executesql(f"{query};")
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
                db.executesql(f"{query};")
                query = ""

        db.commit()

        QueryChapter.updateQCindex(vr, query_id, uptodate=True)

    def sharing(self):
        """Receives a new sharing status of a query and saves it to the database.
        """
        Check = current.Check
        Query = self.Query

        msgs = []
        good = False
        modDates = {}
        modCls = {}
        extra = {}

        requestVars = current.request.vars

        for x in [1]:
            query_id = Check.isId("query_id", "q", "query", msgs)
            if query_id is None:
                break
            fieldName = requestVars.fname
            val = requestVars.val
            vr = requestVars.version
            if fieldName is None or fieldName not in {"is_shared", "is_published"}:
                msgs.append(("error", f"Illegal field name {fieldName}"))
                break
            (authorized, msg) = Query.authWrite(query_id)
            if not authorized:
                msgs.append(("error", msg))
                break
            (good, modDates, modCls, extra) = self.putSharing(
                vr, query_id, fieldName, val, msgs
            )
        return dict(
            data=json.dumps(
                dict(
                    msgs=msgs, good=good, modDates=modDates, modCls=modCls, extra=extra
                )
            )
        )

    def putSharing(self, vr, query_id, fname, val, msgs):
        auth = current.auth
        db = current.db
        Check = current.Check
        now = current.request.utcnow

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
                sql = dedent(
                    f"""
                    select count(*)
                    from query_exe
                    where query_id = {query_id} and is_published = 'T'
                    ;
                    """
                )
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
                    sql = dedent(
                        f"""
                        select executed_on, modified_on as xmodified_on
                        from query_exe
                        where query_id = {query_id} and version = '{vr}'
                        ;
                        """
                    )
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
                    sql = dedent(
                        f"""
                        select is_shared from query where id = {query_id}
                        ;
                        """
                    )
                    pv = db.executesql(sql)
                    is_shared = pv is not None and len(pv) == 1 and pv[0][0] == "T"
                    if not is_shared:
                        (modDateFld, modDate) = self.putShared(
                            myId, query_id, "T", msgs
                        )
                        modDates[modDateFld] = modDate
                        extra["is_shared"] = ("checked", True)
                else:
                    sql = dedent(
                        f"""
                        select published_on
                        from query_exe
                        where query_id = {query_id} and version = '{vr}'
                        ;
                        """
                    )
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
                (modDateFld, modDate) = self.putShared(myId, query_id, valsql, msgs)
            else:
                (modDateFld, modDate) = self.putPublished(
                    myId, vr, query_id, valsql, msgs
                )
            modDates[modDateFld] = modDate
        return (good, modDates, modCls, extra)

    def putShared(self, myId, query_id, valsql, msgs):
        Caching = current.Caching
        QueryChapter = self.QueryChapter
        db = current.db
        VERSIONS = current.VERSIONS

        modDate = None
        modDateFld = "shared_on"
        table = "query"
        fname = "is_shared"
        Caching.clear(r"^items_q_")
        fieldval = f" {fname} = '{valsql}'"
        now = current.request.utcnow
        modDate = now.replace(microsecond=0) if valsql == "T" else None
        modDateSql = "null" if modDate is None else f" '{modDate}'"
        fieldval += f", {modDateFld} = {modDateSql} "
        sql = dedent(
            f"""
            update {table} set{fieldval} where id = {query_id}
            ;
            """
        )
        db.executesql(sql)

        db.commit()

        for vr in VERSIONS:
            QueryChapter.updateQCindex(vr, query_id)

        thismsg = "modified"
        thismsg = "shared" if valsql == "T" else "UNshared"
        msgs.append(("good", thismsg))
        return (modDateFld, str(modDate) if modDate else NULLDT)

    def putPublished(self, myId, vr, query_id, valsql, msgs):
        Caching = current.Caching
        QueryChapter = self.QueryChapter
        db = current.db

        modDate = None
        modDateFld = "published_on"
        table = "query_exe"
        fname = "is_published"
        Caching.clear(f"^items_q_{vr}_")
        self.verifyVersion(vr, query_id)
        fieldval = f" {fname} = '{valsql}'"
        now = current.request.utcnow
        modDate = now.replace(microsecond=0) if valsql == "T" else None
        modDateSql = "null" if modDate is None else f" '{modDate}'"
        fieldval += f", {modDateFld} = {modDateSql} "
        sql = dedent(
            f"""
            update {table}
            set{fieldval}
            where query_id = {query_id} and version = '{vr}'
            ;
            """
        )
        db.executesql(sql)
        db.commit()

        thismsg = "modified"
        thismsg = "published" if valsql == "T" else "UNpublished"
        QueryChapter.updatePubStatus(vr, query_id, valsql == "T")
        msgs.append(("good", thismsg))
        return (modDateFld, str(modDate) if modDate else NULLDT)

    def putMeta(self, vr, query_id, fields, fieldsExe):
        Caching = current.Caching
        db = current.db
        doCommit = False

        if len(fields):
            fieldRep = ", ".join(
                f" {f} = '{fields[f]}'" for f in fields if f != "status"
            )
            sql = dedent(
                f"""
                update query set{fieldRep} where id = {query_id}
                ;
                """
            )
            db.executesql(sql)
            doCommit = True
            Caching.clear(r"^items_q_")
        if len(fieldsExe):
            fieldRep = ", ".join(
                f" {f} = '{fieldsExe[f]}'" for f in fieldsExe if f != "status"
            )
            sql = dedent(
                f"""
                update query_exe
                set{fieldRep}
                where query_id = {query_id} and version = '{vr}'
                ;
                """
            )
            db.executesql(sql)
            doCommit = True
            Caching.clear(f"^items_q_{vr}_")

        if doCommit:

            db.commit()

    def putRecord(self):
        """Receives updated record data of a query and stores it in the database.
        """
        Check = current.Check
        Query = self.Query
        auth = current.auth

        requestVars = current.request.vars

        vr = requestVars.version
        nameNew = requestVars.name
        mqlNew = requestVars.mql
        descriptionNew = requestVars.description
        execute = requestVars.execute

        myId = auth.user.id if auth.user is not None else None

        now = current.request.utcnow

        msgs = []
        good = False
        fields = {}
        fieldsExe = {}
        queryRecord = {}

        is_published = False

        for x in [1]:
            query_id = Check.isId("query_id", "q", "query", msgs)
            if query_id is None:
                break
            (authorized, msg) = Query.authWrite(query_id)
            if not authorized:
                msgs.append(("error", msg))
                break

            self.verifyVersion(vr, query_id)
            recordOld = Query.getBasicInfo(vr, query_id)

            if recordOld is None or len(recordOld) == 0:
                msgs.append(("error", f"No query with id {query_id}"))
                break
            valsOld = recordOld[0]
            is_published = valsOld["is_published"] == "T"

            if not is_published:
                if valsOld["name"] != nameNew:
                    valSql = Check.isName("q", query_id, myId, nameNew, msgs)
                    if valSql is None:
                        break
                    fields["name"] = valSql
                    fields["modified_on"] = now
                if valsOld["mql"] != mqlNew:
                    msgs.append(("warning", "query body modified"))
                    valSql = Check.isMql("q", mqlNew, msgs)
                    if valSql is None:
                        break
                    fieldsExe["mql"] = valSql
                    fieldsExe["modified_on"] = now
                else:
                    msgs.append(("good", "same query body"))
            else:
                msgs.append(
                    (
                        "warning",
                        (
                            "only the description can been saved"
                            "because this is a published query execution"
                        ),
                    )
                )
            if valsOld["description"] != descriptionNew:
                valSql = Check.isDescription("q", descriptionNew, msgs)
                if valSql is None:
                    break
                fields["description"] = valSql
                fields["modified_on"] = now
            good = True
        if good:
            execute = not is_published and execute
            exeGood = True
            if execute == "true":
                (
                    exeGood,
                    limitExceeded,
                    nResults,
                    exeSlots,
                    theseMsgs,
                    emdrosVersion,
                ) = mql(vr, mqlNew)
                if exeGood and not limitExceeded:
                    self.putSlots(vr, query_id, exeSlots)
                    fieldsExe["executed_on"] = now
                    fieldsExe["eversion"] = emdrosVersion
                    nResultSlots = countSlots(exeSlots)
                    fieldsExe["results"] = nResults
                    fieldsExe["resultmonads"] = nResultSlots
                    msgs.append(("good", "Query executed"))
                else:
                    self.putSlots(vr, query_id, [])
                msgs.extend(theseMsgs)
            self.putMeta(vr, query_id, fields, fieldsExe)
            queryRecord = Query.getInfo(
                auth.user is not None,
                query_id,
                vr,
                msgs,
                withIds=False,
                singleVersion=False,
                po=True,
            )

        emdrosVersionsOld = dict((x, 1) for x in EMDROS_VERSIONS[0:-1])
        return dict(
            data=json.dumps(
                dict(
                    msgs=msgs,
                    good=good and exeGood,
                    query=queryRecord,
                    emdrosVersionsOld=emdrosVersionsOld,
                )
            )
        )

    def verifyVersion(self, vr, query_id):
        db = current.db

        existVersion = db.executesql(
            dedent(
                f"""
                select id from query_exe
                where version = '{vr}' and query_id = {query_id}
                ;
                """
            )
        )
        if existVersion is None or len(existVersion) == 0:
            db.executesql(
                dedent(
                    f"""
                insert into query_exe
                (id, version, query_id) values (null, '{vr}', {query_id})
                ;
                """
                )
            )
            db.commit()
