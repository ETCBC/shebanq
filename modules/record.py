from textwrap import dedent
import json

from gluon import current

from constants import TPS
from helpers import iDecode


class RECORD:
    """Handles record data.

    This is about some aspects of query and note records and
    organization and project records by which they are organized.
    And it is about word records.

    It is called by controllers that fetch sidebar material,
    see [M:RECORD.body][record.RECORD.body].
    """

    def __init__(self):
        pass

    def authWriteGeneric(self, label):
        auth = current.auth

        authorized = auth.user is not None
        errorMessage = f"You have no access to create/modify a {label}"
        return (authorized, "" if authorized else errorMessage)

    def authReadGeneric(self, label):
        authorized = True
        errorMessage = ""
        return (authorized, errorMessage)

    def authRead(self, mr, qw, iidRep):

        if mr == "m":
            return (True, "")
        if qw == "w":
            return (True, "")
        if qw == "n":
            if not iidRep:
                return (False, f"Not a valid note id: {iidRep}")
            return (True, "")
        if qw == "q":
            if iidRep is not None:
                (iid, keywords) = iDecode(qw, iidRep)
                if iid > 0:
                    Query = self.Query
                    return Query.authRead(iid)
            return (False, f"Not a valid query id: {iidRep}")
        return (None, f"Not a valid id: {iidRep}")

    def body(self):
        """Produce data that will get sidebar material later via AJAX.

        !!! caution "Web2py device"
            We use a
            [Web2py device]({{web2pyComponents}})
            here that shields the mechanics of an AJAX call.
            That leads to code that is not very clear.

            These calls are hidden in Web2py javascript, and you will
            not find them in the SHEBANQ client app code.

        This is where the controllers
        [C:hebrew.sidewordbody][controllers.hebrew.sidewordbody],
        [C:hebrew.sidequerybody][controllers.hebrew.sidequerybody] and
        [C:hebrew.sidenotebody][controllers.hebrew.sidenotebody]
        will be used.

        These calls are used when the user requests a **record**
        page directly. The Web2py device takes care that when the sidebar
        is editable, the edits will be submitted via AJAX.
        So far so good.

        However, when a user navigates between **material** pages and **record**
        pages, the pages are not served from scratch, and new sidebar material
        has to be fetched through AJAX as well.

        In the SHEBANQ code we do these AJAX calls explicitly
        client code: [{sidecontent.fetch}][sidecontentfetch].

        Since I was not able to use the Web2py approach for this part of the use case,
        it is probably a good idea ditch this usage of the Web2py mechanism
        altogether in favour of the more explicit way, which is already in our code.
        Now we have two ways of doing the same thing!
        My apologies.
        """  # noqa E501

        Check = current.Check
        LOAD = current.LOAD

        iidRep = Check.field("material", "", "iid")
        vr = Check.field("material", "", "version")
        mr = Check.field("material", "", "mr")
        qw = Check.field("material", "", "qw")

        kind = "word" if qw == "w" else "query" if qw == "q" else "note"

        (authorized, msg) = self.authRead(mr, qw, iidRep)
        if authorized:
            msg = f"fetching {kind}"
        return dict(
            load=LOAD(
                "hebrew",
                f"side{kind}body",
                extension="load",
                vars=dict(mr="r", qw="w", version=vr, iid=iidRep),
                ajax=False,
                ajax_trap=True,
                target=f"{kind}body",
                content=msg,
            )
        )

    def setItem(self):
        """Saves a record to the database.

        Meant for: objects that organize the notes and query overviews:
        organizations and projects.
        Can also save query records.

        !!! hint "Note records and word records"
            Word records are read-only and will never be saved.

            There are no such things as note records.
            Notes are organized in sets bases on keywords and authoring users,
            but a notes set does not have an embodiment as record in the database.
        """

        Check = current.Check
        auth = current.auth

        msgs = []
        orgRecord = {}
        projectRecord = {}
        good = False
        orgGood = False
        projectGood = False
        obj_id = None
        label = None
        table = None
        fields = None

        myId = auth.user.id if auth.user is not None else None

        requestVars = current.request.vars

        for x in [1]:
            tp = requestVars.tp
            if tp not in TPS:
                msgs.append(("error", f"unknown type {tp}!"))
                break
            (label, table) = TPS[tp]
            obj_id = Check.isId("obj_id", tp, label, msgs)
            upd = requestVars.upd
            if obj_id is None:
                break
            if upd not in {"true", "false"}:
                msgs.append(("error", f"invalid instruction {upd}!"))
                break
            upd = True if upd == "true" else False
            if upd and not myId:
                msgs.append(("error", "for updating you have to be logged in!"))
                break
            fields = ["name"]

            if tp == "q":
                Query = self.Query
                fields.append("organization")
                fields.append("project")
            else:
                fields.append("website")
            if upd:
                (authorized, msg) = (
                    Query.authWrite(obj_id)
                    if tp == "q"
                    else self.authWriteGeneric(label)
                )
            else:
                (authorized, msg) = (
                    Query.authRead(obj_id) if tp == "q" else self.authReadGeneric(label)
                )
            if not authorized:
                msgs.append(("error", msg))
                break
            if upd:
                if tp == "q":
                    subfields = ["name", "website"]
                    fieldValues = [requestVars.name]
                    doNewOrg = requestVars.doNewOrg
                    doNewProject = requestVars.doNewProject
                    if doNewOrg not in {"true", "false"}:
                        msgs.append(
                            (
                                "error",
                                f"invalid instruction for organization {doNewOrg}!",
                            )
                        )
                        break
                    doNewOrg = doNewOrg == "true"
                    if doNewProject not in {"true", "false"}:
                        msgs.append(
                            (
                                "error",
                                f"invalid instruction for project {doNewProject}!",
                            )
                        )
                        break
                    doNewProject = doNewProject == "true"
                    orgGood = True
                    if doNewOrg:
                        (orgGood, org_id) = self.update(
                            "o",
                            0,
                            myId,
                            subfields,
                            [requestVars.org_name, requestVars.org_website],
                            msgs,
                        )
                        if orgGood:
                            orgRecord = dict(
                                id=org_id,
                                name=requestVars.org_name,
                                website=requestVars.org_website,
                            )
                    else:
                        org_id = Check.isId("org_id", "o", TPS["o"][0], msgs)
                    projectGood = True
                    if doNewProject:
                        (projectGood, project_id) = self.update(
                            "p",
                            0,
                            myId,
                            subfields,
                            [requestVars.project_name, requestVars.project_website],
                            msgs,
                        )
                        if projectGood:
                            projectRecord = dict(
                                id=project_id,
                                name=requestVars.project_name,
                                website=requestVars.project_website,
                            )
                    else:
                        project_id = Check.isId("project_id", "p", TPS["o"][0], msgs)
                    if not orgGood or not projectGood:
                        break
                    if org_id is None or project_id is None:
                        break
                    fieldValues.extend([org_id, project_id])
                else:
                    fieldValues = [requestVars[field] for field in fields]

                (good, obj_idNew) = self.update(
                    tp, obj_id, myId, fields, fieldValues, msgs
                )
                if not good:
                    break
                obj_id = obj_idNew
            else:
                good = True

        record = self.make(tp, label, table, fields, obj_id, good, msgs)

        return dict(
            data=json.dumps(
                dict(
                    record=record,
                    orgRecord=orgRecord,
                    projectRecord=projectRecord,
                    msgs=msgs,
                    good=good,
                    orgGood=orgGood,
                    projectGood=projectGood,
                )
            )
        )

    def make(self, tp, label, table, fields, obj_id, good, msgs):
        db = current.db

        record = {}

        if good:
            dbRecord = None
            if tp == "q":
                if obj_id == 0:
                    dbRecord = [0, "", 0, "", "", 0, "", ""]
                else:
                    Query = self.Query
                    dbRecord = Query.getTreeInfo(obj_id)
            else:
                if obj_id == 0:
                    dbRecord = [0, "", ""]
                else:
                    dbRecord = db.executesql(
                        dedent(
                            f"""
                            select {",".join(fields)}
                            from {table}
                            where id = {obj_id}
                            ;
                            """
                        ),
                        as_dict=True,
                    )
            if dbRecord:
                record = dbRecord[0]
            else:
                msgs.append(("error", f"No {label} with id {obj_id}"))

        return record

    def update(self, tp, obj_id, myId, fields, fieldValues, msgs):
        Check = current.Check
        db = current.db

        fieldsUpd = {}
        good = False
        (label, table) = TPS[tp]
        useValues = {}
        for i in range(len(fields)):
            field = fields[i]
            value = fieldValues[i]
            useValues[field] = value

        now = current.request.utcnow

        for x in [1]:
            valSql = Check.isName(
                tp,
                obj_id,
                myId,
                useValues["name"],
                msgs,
            )
            if valSql is None:
                break
            fieldsUpd["name"] = valSql
            if tp == "q":
                val = Check.isId(
                    "org_id",
                    "o",
                    TPS["o"][0],
                    msgs,
                    valrep=str(useValues["organization"]),
                )
                if val is None:
                    break
                valSql = Check.isRel("o", val, msgs)
                if valSql is None:
                    break
                fieldsUpd["organization"] = valSql
                val = Check.isId(
                    "project_id",
                    "p",
                    TPS["p"][0],
                    msgs,
                    valrep=str(useValues["project"]),
                )
                valSql = Check.isRel("p", val, msgs)
                if valSql is None:
                    break
                fieldsUpd["project"] = valSql
                fld = "modified_on"
                fieldsUpd[fld] = now
                fields.append(fld)
                if obj_id == 0:
                    fld = "created_on"
                    fieldsUpd[fld] = now
                    fields.append(fld)
                    fld = "created_by"
                    fieldsUpd[fld] = myId
                    fields.append(fld)
            else:
                valSql = Check.isWebsite(tp, useValues["website"], msgs)
                if valSql is None:
                    break
                fieldsUpd["website"] = valSql
            good = True
        if good:
            if obj_id:
                fieldVals = [f" {f} = '{fieldsUpd[f]}'" for f in fields]
                sql = dedent(
                    f"""
                    update {table}
                    set{",".join(fieldVals)}
                    where id = {obj_id}
                    ;
                    """
                )
                thisMsg = "updated"
            else:
                fieldVals = [f"'{fieldsUpd[f]}'" for f in fields]
                sql = dedent(
                    f"""
                    insert into {table}
                    ({",".join(fields)})
                    values ({",".join(fieldVals)})
                    ;
                    """
                )
                thisMsg = f"{label} added"

            db.executesql(sql)

            db.commit()

            if obj_id == 0:
                obj_id = db.executesql(
                    dedent(
                        """
                    select last_insert_id() as x
                    ;
                    """
                    )
                )[0][0]

            msgs.append(("good", thisMsg))
        return (good, obj_id)


class RECORDQUERY(RECORD):
    def __init__(self, Query):
        super().__init__()
        self.Query = Query
