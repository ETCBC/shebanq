from textwrap import dedent
import collections
import json

from gluon import current

from helpers import hEsc, iEncode, formatVersion


class NOTETREE:
    def __init__(self):
        pass

    def get(self):
        """Get the metadata of all queries and deliver it as JSON.
        """

        auth = current.auth
        NOTE_DB = current.NOTE_DB
        VERSION_ORDER = current.VERSION_ORDER
        VERSION_INDEX = current.VERSION_INDEX

        myId = None
        if auth.user:
            myId = auth.user.id
        objInfo = collections.defaultdict(lambda: {})

        def titleBadge(obj_id, objType, tot):
            name = objInfo[objType][obj_id] if objType is not None else "Shared Notes"
            badge = ""
            if tot != 0:
                badge = f'<span class="total special"> {tot}</span>'
            return f'<span n="1">{hEsc(name)}</span><span class="brn">({badge})</span>'

        condition = (
            dedent(
                """
                where note.is_shared = 'T'
                """
            )
            if myId is None
            else dedent(
                f"""
                where note.is_shared = 'T' or note.created_by = {myId}
                """
            )
        )

        projectNoteSql = dedent(
            f"""
            select
                count(note.id) as amount,
                note.version,
                note.keywords,
                concat(auth_user.first_name, ' ', auth_user.last_name) as uname,
                auth_user.id as user_id
            from note
            inner join shebanq_web.auth_user
            on note.created_by = shebanq_web.auth_user.id
            {condition}
            group by auth_user.id, note.keywords, note.version
            order by shebanq_web.auth_user.last_name,
            shebanq_web.auth_user.first_name, note.keywords
            ;
            """
        )

        projectNote = NOTE_DB.executesql(projectNoteSql)
        projectNotes = collections.OrderedDict()
        for (amount, nvr, keywordList, uname, user_id) in projectNote:
            for keywords in set(keywordList.strip().split()):
                key_id = iEncode("n", user_id, keywords=keywords)
                if key_id not in projectNotes:
                    projectNotes[key_id] = {
                        "": (uname, user_id, keywords),
                        "v": [0 for v in VERSION_ORDER],
                    }
                projectNotes[key_id]["v"][VERSION_INDEX[nvr]] = amount

        tree = collections.OrderedDict()
        countSet = collections.defaultdict(lambda: set())
        countUser = collections.defaultdict(lambda: 0)
        count = 0
        for key_id in projectNotes:
            projectNoteInfo = projectNotes[key_id]
            (uname, user_id, noteName) = projectNoteInfo[""]
            countSet["u"].add(user_id)
            countSet["n"].add(key_id)
            objInfo["u"][user_id] = uname
            tree.setdefault(user_id, []).append(key_id)
            count += 1
            countUser[user_id] += 1

        objInfo["u"][0] = ""
        objInfo["n"] = projectNotes

        categoryCount = dict((x[0], len(x[1])) for x in countSet.items())
        categoryCount["user_id"] = myId
        title = titleBadge(None, None, count)
        dest = [dict(title=str(title), folder=True, children=[], data=categoryCount)]
        curDest = dest[-1]["children"]
        curSource = tree
        for user_id in curSource:
            userTotal = countUser[user_id]
            userTitle = titleBadge(user_id, "u", userTotal)
            curDest.append(dict(title=str(userTitle), folder=True, children=[]))
            curUserDest = curDest[-1]["children"]
            curUserSource = curSource[user_id]
            for key_id in curUserSource:
                projectNoteInfo = objInfo["n"][key_id]
                (uname, user_id, noteName) = projectNoteInfo[""]
                noteVersions = projectNoteInfo["v"]
                versionRep = " ".join(
                    formatVersion("n", key_id, v, noteVersions[VERSION_INDEX[v]])
                    for v in VERSION_ORDER
                )
                curUserDest.append(
                    dict(
                        title=(
                            f"""{versionRep} <a
class="n keywords" n="1" key_id="{key_id}" href="#"
>{hEsc(noteName)}</a> <a class="md" href="#"></a>"""
                        ),
                        key=f"n{key_id}",
                        folder=False,
                    ),
                )
        return dict(data=json.dumps(dest))
