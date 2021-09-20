import collections
import json

from helpers import hEsc, iEncode, formatVersion


class NOTETREE:
    def __init__(
        self,
        auth,
        NOTE_DB,
        VERSION_ORDER,
        VERSION_INDEX,
    ):
        self.auth = auth
        self.NOTE_DB = NOTE_DB
        self.VERSION_ORDER = VERSION_ORDER
        self.VERSION_INDEX = VERSION_INDEX

    def get(self, now):
        auth = self.auth
        NOTE_DB = self.NOTE_DB
        VERSION_ORDER = self.VERSION_ORDER
        VERSION_INDEX = self.VERSION_INDEX

        myId = None
        if auth.user:
            myId = auth.user.id
        linfo = collections.defaultdict(lambda: {})

        def titleBadge(lid, ltype, tot):
            name = linfo[ltype][lid] if ltype is not None else "Shared Notes"
            badge = ""
            if tot != 0:
                badge = f'<span class="total special"> {tot}</span>'
            return f'<span n="1">{hEsc(name)}</span><span class="brn">({badge})</span>'

        condition = (
            """
where note.is_shared = 'T'
"""
            if myId is None
            else f"""
where note.is_shared = 'T' or note.created_by = {myId}
"""
        )

        projectNoteSql = f"""
select
    count(note.id) as amount,
    note.version,
    note.keywords,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname,
    auth_user.id as uid
from note
inner join shebanq_web.auth_user on note.created_by = shebanq_web.auth_user.id
{condition}
group by auth_user.id, note.keywords, note.version
order by shebanq_web.auth_user.last_name,
shebanq_web.auth_user.first_name, note.keywords
;
"""

        projectNote = NOTE_DB.executesql(projectNoteSql)
        projectNotes = collections.OrderedDict()
        for (amount, nvr, kws, uname, uid) in projectNote:
            for kw in set(kws.strip().split()):
                keyId = iEncode("n", uid, kw=kw)
                if keyId not in projectNotes:
                    projectNotes[keyId] = {
                        "": (uname, uid, kw),
                        "v": [0 for v in VERSION_ORDER],
                    }
                projectNotes[keyId]["v"][VERSION_INDEX[nvr]] = amount

        tree = collections.OrderedDict()
        countSet = collections.defaultdict(lambda: set())
        countUser = collections.defaultdict(lambda: 0)
        count = 0
        for keyId in projectNotes:
            projectNoteInfo = projectNotes[keyId]
            (uname, uid, noteName) = projectNoteInfo[""]
            countSet["u"].add(uid)
            countSet["n"].add(keyId)
            linfo["u"][uid] = uname
            tree.setdefault(uid, []).append(keyId)
            count += 1
            countUser[uid] += 1

        linfo["u"][0] = ""
        linfo["n"] = projectNotes

        categoryCount = dict((x[0], len(x[1])) for x in countSet.items())
        categoryCount["uid"] = myId
        title = titleBadge(None, None, count)
        dest = [dict(title=str(title), folder=True, children=[], data=categoryCount)]
        curDest = dest[-1]["children"]
        curSource = tree
        for uid in curSource:
            userTotal = countUser[uid]
            userTitle = titleBadge(uid, "u", userTotal)
            curDest.append(dict(title=str(userTitle), folder=True, children=[]))
            curUserDest = curDest[-1]["children"]
            curUserSource = curSource[uid]
            for keyId in curUserSource:
                projectNoteInfo = linfo["n"][keyId]
                (uname, uid, noteName) = projectNoteInfo[""]
                noteVersions = projectNoteInfo["v"]
                versionRep = " ".join(
                    formatVersion("n", keyId, v, noteVersions[VERSION_INDEX[v]])
                    for v in VERSION_ORDER
                )
                curUserDest.append(
                    dict(
                        title=(
                            f"""{versionRep} <a
class="n nt_kw" n="1" nkid="{keyId}" href="#">"""
                            '{hEsc(noteName)}</a> <a class="md" href="#"></a>'
                        ),
                        key=f"n{keyId}",
                        folder=False,
                    ),
                )
        return dict(data=json.dumps(dest))
