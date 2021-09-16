import collections
import json

from constants import PUBLISH_FREEZE
from helpers import h_esc, iid_encode, formatVersion


class QUERYTREE:
    def __init__(self, auth, db, version_order, version_index):
        self.auth = auth
        self.db = db
        self.version_order = version_order
        self.version_index = version_index

    def get(self, now):
        auth = self.auth
        db = self.db
        version_order = self.version_order
        version_index = self.version_index

        myid = None
        if auth.user:
            myid = auth.user.id
        linfo = collections.defaultdict(lambda: {})

        def title_badge(lid, ltype, publ, good, num, tot):
            name = linfo[ltype][lid] if ltype is not None else "Shared Queries"
            nums = []
            if publ != 0:
                nums.append(f'<span class="special fa fa-quote-right"> {publ}</span>')
            if good != 0:
                nums.append(f'<span class="good fa fa-gears"> {good}</span>')
            badge = ""
            if len(nums) == 0:
                nrep = ", ".join(nums)
                if tot == num:
                    badge = f'<span class="total">{nrep}</span>'
                else:
                    badge = f'{nrep} of <span class="total">{tot}</span>'
            else:
                if tot == num:
                    badge = f'{nrep} of <span class="total">{num}</span>'
                else:
                    badge = f'{nrep} of {num} of all <span class="total">{tot}</span>'
            rename = ""
            select = ""
            if ltype in {"o", "p"}:
                if myid is not None:
                    if lid:
                        rename = f'<a class="r_{ltype}" lid="{lid}" href="#"></a>'
                    select = f'<a class="s_{ltype} fa fa-lg" lid="{lid}" href="#"></a>'
                else:
                    if lid:
                        rename = f'<a class="v_{ltype}" lid="{lid}" href="#"></a>'
            return f"""{select}
<span n="1">{h_esc(name)}</span><span class="brq">({badge})</span> {rename}"""

        condition = (
            """
where query.is_shared = 'T'
"""
            if myid is None
            else f"""
where query.is_shared = 'T' or query.created_by = {myid}
"""
        )

        pqueryx_sql = f"""
select
    query_exe.query_id,
    query_exe.version,
    query_exe.is_published,
    query_exe.published_on,
    query_exe.modified_on,
    query_exe.executed_on
from query_exe
inner join query on query.id = query_exe.query_id
{condition};
"""

        pquery_sql = f"""
select
    query.id as qid,
    organization.name as oname, organization.id as oid,
    project.name as pname, project.id as pid,
    concat(auth_user.first_name, ' ', auth_user.last_name) as uname,
    auth_user.id as uid,
    query.name as qname, query.is_shared as is_shared
from query
inner join auth_user on query.created_by = auth_user.id
inner join project on query.project = project.id
inner join organization on query.organization = organization.id
{condition}
order by organization.name,
project.name,
auth_user.last_name,
auth_user.first_name,
query.name
;
"""

        pquery = db.executesql(pquery_sql)
        pqueryx = db.executesql(pqueryx_sql)
        pqueries = collections.OrderedDict()
        for (qid, oname, oid, pname, pid, uname, uid, qname, qshared) in pquery:
            qsharedstatus = qshared == "T"
            qownstatus = uid == myid
            pqueries[qid] = {
                "": (
                    oname,
                    oid,
                    pname,
                    pid,
                    uname,
                    uid,
                    qname,
                    qsharedstatus,
                    qownstatus,
                ),
                "publ": False,
                "good": False,
                "v": [4 for v in version_order],
            }
        for (qid, vr, qispub, qpub, qmod, qexe) in pqueryx:
            qinfo = pqueries[qid]
            qexestatus = None
            if qexe:
                qexestatus = qexe >= qmod
            qpubstatus = (
                False
                if qispub != "T"
                else None
                if qpub > now - PUBLISH_FREEZE
                else True
            )
            qstatus = (
                1
                if qpubstatus
                else 2
                if qpubstatus is None
                else 3
                if qexestatus
                else 4
                if qexestatus is None
                else 5
            )
            qinfo["v"][version_index[vr]] = qstatus
            if qpubstatus or qpubstatus is None:
                qinfo["publ"] = True
            if qexestatus:
                qinfo["good"] = True

        porg_sql = """
select name, id from organization order by name
;
"""
        porg = db.executesql(porg_sql)

        pproj_sql = """
select name, id from project order by name
;
"""
        pproj = db.executesql(pproj_sql)

        tree = collections.OrderedDict()
        countset = collections.defaultdict(lambda: set())
        counto = collections.defaultdict(lambda: 0)
        counto_publ = collections.defaultdict(lambda: 0)
        counto_good = collections.defaultdict(lambda: 0)
        counto_tot = collections.defaultdict(lambda: 0)
        countp = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        countp_publ = collections.defaultdict(
            lambda: collections.defaultdict(lambda: 0)
        )
        countp_good = collections.defaultdict(
            lambda: collections.defaultdict(lambda: 0)
        )
        countp_tot = collections.defaultdict(lambda: 0)
        countu = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countu_publ = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countu_good = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countu_tot = collections.defaultdict(lambda: 0)
        count = 0
        count_publ = 0
        count_good = 0
        for qid in pqueries:
            pqinfo = pqueries[qid]
            (oname, oid, pname, pid, uname, uid, qname, qshared, qown) = pqinfo[""]
            qpubl = pqinfo["publ"]
            qgood = pqinfo["good"]
            countset["o"].add(oid)
            countset["p"].add(pid)
            countset["u"].add(uid)
            countset["q"].add(qid)
            linfo["o"][oid] = oname
            linfo["p"][pid] = pname
            linfo["u"][uid] = uname
            if qown:
                countset["m"].add(qid)
            if not qshared:
                countset["r"].add(qid)
            if qpubl:
                countu_publ[oid][pid][uid] += 1
                countp_publ[oid][pid] += 1
                counto_publ[oid] += 1
                count_publ += 1
            if qgood:
                countu_good[oid][pid][uid] += 1
                countp_good[oid][pid] += 1
                counto_good[oid] += 1
                count_good += 1
            tree.setdefault(oid, collections.OrderedDict()).setdefault(
                pid, collections.OrderedDict()
            ).setdefault(uid, []).append(qid)
            count += 1
            counto[oid] += 1
            countp[oid][pid] += 1
            countu[oid][pid][uid] += 1
            counto_tot[oid] += 1
            countp_tot[pid] += 1
            countu_tot[uid] += 1

        linfo["o"][0] = "Projects without Queries"
        linfo["p"][0] = "New Project"
        linfo["u"][0] = ""
        linfo["q"] = pqueries
        counto[0] = 0
        countp[0][0] = 0
        for (oname, oid) in porg:
            if oid in linfo["o"]:
                continue
            countset["o"].add(oid)
            linfo["o"][oid] = oname
            tree[oid] = collections.OrderedDict()

        for (pname, pid) in pproj:
            if pid in linfo["p"]:
                continue
            countset["o"].add(0)
            countset["p"].add(pid)
            linfo["p"][pid] = pname
            tree.setdefault(0, collections.OrderedDict())[
                pid
            ] = collections.OrderedDict()

        ccount = dict((x[0], len(x[1])) for x in countset.items())
        ccount["uid"] = myid
        title = title_badge(None, None, count_publ, count_good, count, count)
        dest = [dict(title=str(title), folder=True, children=[], data=ccount)]
        curdest = dest[-1]["children"]
        cursource = tree
        for oid in cursource:
            onum = counto[oid]
            opubl = counto_publ[oid]
            ogood = counto_good[oid]
            otot = counto_tot[oid]
            otitle = title_badge(oid, "o", opubl, ogood, onum, otot)
            curdest.append(dict(title=str(otitle), folder=True, children=[]))
            curodest = curdest[-1]["children"]
            curosource = cursource[oid]
            for pid in curosource:
                pnum = countp[oid][pid]
                ppubl = countp_publ[oid][pid]
                pgood = countp_good[oid][pid]
                ptot = countp_tot[pid]
                ptitle = title_badge(pid, "p", ppubl, pgood, pnum, ptot)
                curodest.append(dict(title=str(ptitle), folder=True, children=[]))
                curpdest = curodest[-1]["children"]
                curpsource = curosource[pid]
                for uid in curpsource:
                    unum = countu[oid][pid][uid]
                    upubl = countu_publ[oid][pid][uid]
                    ugood = countu_good[oid][pid][uid]
                    utot = countu_tot[uid]
                    utitle = title_badge(uid, "u", upubl, ugood, unum, utot)
                    curpdest.append(dict(title=str(utitle), folder=True, children=[]))
                    curudest = curpdest[-1]["children"]
                    curusource = curpsource[uid]
                    for qid in curusource:
                        pqinfo = linfo["q"][qid]
                        (
                            oname,
                            oid,
                            pname,
                            pid,
                            uname,
                            uid,
                            qname,
                            qshared,
                            qown,
                        ) = pqinfo[""]
                        qpubl = pqinfo["publ"]
                        qgood = pqinfo["good"]
                        qversions = pqinfo["v"]
                        qorep = "r" if qown else "v"
                        qmrep = ("qmy" if qown else "",)
                        qshrep = "" if qshared else "qpriv"
                        qidrep = (iid_encode("q", qid),)
                        rename = f'<a class="{qorep}_q" lid="{qidrep}" href="#"></a>'
                        vrep = " ".join(
                            formatVersion("q", qid, v, qversions[version_index[v]])
                            for v in version_order
                        )
                        curudest.append(
                            dict(
                                title=(
                                    f'{vrep} <a class="q {qmrep} {qshrep}" '
                                    f'n="1" qid="{qid}" href="#">'
                                    f"{h_esc(qname)}</a> "
                                    f'<a class="md" href="#"></a> {rename}'
                                ),
                                key=f"q{qid}",
                                folder=False,
                            )
                        )
        return dict(data=json.dumps(dest))
