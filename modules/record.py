from constants import TPS
from helpers import iDecode


class RECORD:
    def __init__(self, Check, Query, auth, db):
        self.Check = Check
        self.Query = Query
        self.auth = auth
        self.db = db

    def authWriteGeneric(self, label):
        auth = self.auth

        authorized = auth.user is not None
        errorMessage = f"You have no access to create/modify a {label}"
        return (authorized, "" if authorized else errorMessage)

    def authReadGeneric(self, label):
        authorized = True
        errorMessage = ""
        return (authorized, errorMessage)

    def authRead(self, mr, qw, iidRep):
        Query = self.Query

        if mr == "m":
            return (True, "")
        if qw == "w":
            return (True, "")
        if qw == "n":
            return (True, "")
        if qw == "q":
            if iidRep is not None:
                (iid, keywords) = iDecode(qw, iidRep)
                if iid > 0:
                    return Query.authRead(iid)
            return (False, f"Not a valid query id: {iidRep}")
        return (None, f"Not a valid id: {iidRep}")

    def make(self, tp, label, table, fields, obj_id, good, msgs):
        Query = self.Query
        db = self.db

        record = {}

        if good:
            dbRecord = None
            if tp == "q":
                if obj_id == 0:
                    dbRecord = [0, "", 0, "", "", 0, "", ""]
                else:
                    dbRecord = Query.getTreeInfo(obj_id)
            else:
                if obj_id == 0:
                    dbRecord = [0, "", ""]
                else:
                    dbRecord = db.executesql(
                        f"""
select {",".join(fields)} from {table} where id = {obj_id}
;
""",
                        as_dict=True,
                    )
            if dbRecord:
                record = dbRecord[0]
            else:
                msgs.append(("error", f"No {label} with id {obj_id}"))

        return record

    def update(self, tp, obj_id, myId, fields, fieldValues, now, msgs):
        Check = self.Check
        db = self.db

        fieldsUpd = {}
        good = False
        (label, table) = TPS[tp]
        useValues = {}
        for i in range(len(fields)):
            field = fields[i]
            value = fieldValues[i]
            useValues[field] = value

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
                sql = (
                    f"""update {table} set{",".join(fieldVals)} where id = {obj_id};"""
                )
                thisMsg = "updated"
            else:
                fieldVals = [f"'{fieldsUpd[f]}'" for f in fields]
                sql = f"""
insert into {table} ({",".join(fields)}) values ({",".join(fieldVals)})
;
"""
                thisMsg = f"{label} added"
            db.executesql(sql)
            if obj_id == 0:
                obj_id = db.executesql(
                    """
select last_insert_id() as x
;
"""
                )[0][0]

            msgs.append(("good", thisMsg))
        return (good, obj_id)
