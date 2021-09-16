import collections
import json

from helpers import h_esc, iid_encode, formatVersion


class NOTETREE:
    def __init__(
        self,
        auth,
        note_db,
        version_order,
        version_index,
    ):
        self.auth = auth
        self.note_db = note_db
        self.version_order = version_order
        self.version_index = version_index

    def get(self, now):
        auth = self.auth
        note_db = self.note_db
        version_order = self.version_order
        version_index = self.version_index

        myid = None
        if auth.user:
            myid = auth.user.id
        linfo = collections.defaultdict(lambda: {})

        def title_badge(lid, ltype, tot):
            name = linfo[ltype][lid] if ltype is not None else "Shared Notes"
            badge = ""
            if tot != 0:
                badge = f'<span class="total special"> {tot}</span>'
            return f'<span n="1">{h_esc(name)}</span><span class="brn">({badge})</span>'

        condition = (
            """
where note.is_shared = 'T'
"""
            if myid is None
            else f"""
where note.is_shared = 'T' or note.created_by = {myid}
"""
        )

        pnote_sql = f"""
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

        pnote = note_db.executesql(pnote_sql)
        pnotes = collections.OrderedDict()
        for (amount, nvr, kws, uname, uid) in pnote:
            for kw in set(kws.strip().split()):
                nkid = iid_encode("n", uid, kw=kw)
                if nkid not in pnotes:
                    pnotes[nkid] = {
                        "": (uname, uid, kw),
                        "v": [0 for v in version_order],
                    }
                pnotes[nkid]["v"][version_index[nvr]] = amount

        tree = collections.OrderedDict()
        countset = collections.defaultdict(lambda: set())
        countu = collections.defaultdict(lambda: 0)
        count = 0
        for nkid in pnotes:
            pninfo = pnotes[nkid]
            (uname, uid, nname) = pninfo[""]
            countset["u"].add(uid)
            countset["n"].add(nkid)
            linfo["u"][uid] = uname
            tree.setdefault(uid, []).append(nkid)
            count += 1
            countu[uid] += 1

        linfo["u"][0] = ""
        linfo["n"] = pnotes

        ccount = dict((x[0], len(x[1])) for x in countset.items())
        ccount["uid"] = myid
        title = title_badge(None, None, count)
        dest = [dict(title=str(title), folder=True, children=[], data=ccount)]
        curdest = dest[-1]["children"]
        cursource = tree
        for uid in cursource:
            utot = countu[uid]
            utitle = title_badge(uid, "u", utot)
            curdest.append(dict(title=str(utitle), folder=True, children=[]))
            curudest = curdest[-1]["children"]
            curusource = cursource[uid]
            for nkid in curusource:
                pninfo = linfo["n"][nkid]
                (uname, uid, nname) = pninfo[""]
                nversions = pninfo["v"]
                vrep = " ".join(
                    formatVersion("n", nkid, v, nversions[version_index[v]])
                    for v in version_order
                )
                curudest.append(
                    dict(
                        title=(
                            f'{vrep} <a class="n nt_kw" n="1" nkid="{nkid}" href="#">'
                            '{h_esc(nname)}</a> <a class="md" href="#"></a>'
                        ),
                        key=f"n{nkid}",
                        folder=False,
                    ),
                )
        return dict(data=json.dumps(dest))
