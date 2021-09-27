from urllib.parse import urlparse, urlunparse

from gluon import current

from constants import TPS
from helpers import iDecode


class CHECK:
    def __init__(self):
        pass

    def field(self, group, qw, var, default=True):
        ViewDefs = current.ViewDefs
        request = current.request

        requestVar = ("c_" if group == "colormap" else "") + qw + var
        if requestVar == "iid":
            x = request.vars.get("id", request.vars.get("iid", None))
        else:
            x = request.vars.get(requestVar, None)
            if requestVar == "extra":
                x = str(x)
        if type(x) is list:
            x = x[0]
            # this occurs when the same variable occurs multiple times
            # in the request/querystring
        theVar = "0" if group == "colormap" else var
        defaultValue = ViewDefs["settings"][group][qw][theVar] if default else None
        return ViewDefs["validation"][group][qw][theVar](defaultValue, x)

    def fields(self, tp, qw=None):
        ViewDefs = current.ViewDefs

        if qw is None or qw != "n":
            if tp == "txtd":
                hebrewFields = []
                for (line, fields) in ViewDefs["featureLines"]:
                    if self.field("hebrewdata", "", line) == "v":
                        for (f, name, prettyName) in fields:
                            if self.field("hebrewdata", "", f) == "v":
                                hebrewFields.append((name, prettyName))
            else:
                hebrewFields = ViewDefs["featureFields"][tp]
            return hebrewFields
        else:
            hebrewFields = (
                (
                    ("clause_atom", "ca_nr"),
                    ("shebanq_note.note.keywords", "keyw"),
                    ("shebanq_note.note.status", "status"),
                    ("shebanq_note.note.ntext", "note"),
                )
                if tp == "txtp"
                else (
                    ("clause_atom", "ca_nr"),
                    ("clause_atom.text", "ca_txt"),
                    ("shebanq_note.note.keywords", "keyw"),
                    ("shebanq_note.note.status", "status"),
                    ("shebanq_note.note.ntext", "note"),
                    ("shebanq_note.note.created_on", "created_on"),
                    ("shebanq_note.note.modified_on", "modified_on"),
                    (
                        (
                            'if(shebanq_note.note.is_shared = "T", "T", "F") '
                            "as shared"
                        ),
                        "is_shared",
                    ),
                    (
                        (
                            'if(shebanq_note.note.is_published = "T", "T", "F") '
                            "as is_published"
                        ),
                        "is_published",
                    ),
                    (
                        'ifnull(shebanq_note.note.published_on, "") as pub',
                        "published_on",
                    ),
                )
            )
            return hebrewFields

    def isUnique(self, tp, obj_id, val, myId, msgs):
        db = current.db

        result = False
        (label, table) = TPS[tp]
        for x in [1]:
            if tp == "q":
                checkSql = f"""
select id from query where name = '{val}' and query.created_by = {myId}
;
"""
            else:
                checkSql = f"""
select id from {table} where name = '{val}'
;
"""
            try:
                ids = db.executesql(checkSql)
            except Exception:
                msgs.append(("error", f"cannot check the unicity of {val} as {label}!"))
                break
            if len(ids) and (obj_id == 0 or ids[0][0] != int(obj_id)):
                msgs.append(("error", f"the {label} name is already taken!"))
                break
            result = True
        return result

    def isName(self, tp, obj_id, myId, val, msgs):
        label = TPS[tp][0]
        result = None
        for x in [1]:
            if len(val) > 64:
                msgs.append(
                    (
                        "error",
                        f"{label} name is longer than 64 characters!",
                    )
                )
                break
            val = val.strip()
            if val == "":
                msgs.append(
                    ("error", f"{label} name consists completely of white space!")
                )
                break
            val = val.replace("'", "''")
            if not self.isUnique(tp, obj_id, val, myId, msgs):
                break
            result = val
        return result

    def isDescription(self, tp, val, msgs):
        label = TPS[tp][0]
        result = None
        for x in [1]:
            if len(val) > 8192:
                msgs.append(
                    ("error", f"{label} description is longer than 8192 characters!")
                )
                break
            result = val.replace("'", "''")
        return result

    def isMql(self, tp, val, msgs):
        label = TPS[tp][0]
        result = None
        for x in [1]:
            if len(val) > 8192:
                msgs.append(
                    (
                        "error",
                        f"{label} mql is longer than 8192 characters!",
                    )
                )
                break
            result = val.replace("'", "''")
        return result

    def isPublished(self, tp, val, msgs):
        label = TPS[tp][0]
        result = None
        for x in [1]:
            if len(val) > 10 or (len(val) > 0 and not val.isalnum()):
                msgs.append(
                    (
                        "error",
                        f"{label} published status has an invalid value {val}",
                    )
                )
                break
            result = "T" if val == "T" else ""
        return result

    def isWebsite(self, tp, val, msgs):
        label = TPS[tp][0]
        result = None
        for x in [1]:
            if len(val) > 512:
                msgs.append(
                    ("error", f"{label} website is longer than 512 characters!")
                )
                break
            val = val.strip()
            if val == "":
                msgs.append(
                    ("error", f"{label} website consists completely of white space!")
                )
                break
            try:
                urlComps = urlparse(val)
            except ValueError:
                msgs.append(("error", f"invalid syntax in {label} website !"))
                break
            scheme = urlComps.scheme
            if scheme not in {"http", "https"}:
                msgs.append(
                    ("error", f"{label} website does not start with http(s)://")
                )
                break
            netloc = urlComps.netloc
            if "." not in netloc:
                msgs.append(("error", f"no location in {label} website"))
                break
            result = urlunparse(urlComps).replace("'", "''")
        return result

    def isInt(self, var, label, msgs):
        request = current.request

        val = request.vars[var]
        if val is None:
            msgs.append(("error", f"No {label} number given"))
            return None
        if len(val) > 10 or not val.isdigit():
            msgs.append(("error", f"Not a valid {label}"))
            return None
        return int(val)

    def isBool(self, var):
        request = current.request

        val = request.vars[var]
        if (
            val is None
            or len(val) > 10
            or not val.isalpha()
            or val not in {"true", "false"}
            or val == "false"
        ):
            return False
        return True

    def isId(self, var, tp, label, msgs, valrep=None):
        request = current.request

        if valrep is None:
            valrep = request.vars[var]
        if valrep is None:
            msgs.append(("error", f"No {label} id given"))
            return None
        if tp in {"w", "q", "n"}:
            (val, keywords) = iDecode(tp, valrep)
        else:
            val = valrep
            if len(valrep) > 10 or not valrep.isdigit():
                msgs.append(("error", f"Not a valid {label} id"))
                return None
            val = int(valrep)
        if tp == "n":
            return valrep
        return val

    def isRel(self, tp, val, msgs):
        db = current.db

        (label, table) = TPS[tp]
        result = None
        for x in [1]:
            checkSql = f"""
select count(*) as occurs from {table} where id = {val}
;
"""
            try:
                occurs = db.executesql(checkSql)[0][0]
            except Exception:
                msgs.append(
                    (
                        "error",
                        f"cannot check the occurrence of {label} id {val}!",
                    )
                )
                break
            if not occurs:
                if val == 0:
                    msgs.append(("error", f"No {label} chosen!"))
                else:
                    msgs.append(("error", f"There is no {label} {val}!"))
                break
            result = val
        return result


current.Check = CHECK()
