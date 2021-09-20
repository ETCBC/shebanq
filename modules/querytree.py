import collections
import json

from constants import PUBLISH_FREEZE
from helpers import hEsc, iEncode, formatVersion


class QUERYTREE:
    def __init__(self, auth, db, VERSION_ORDER, VERSION_INDEX):
        self.auth = auth
        self.db = db
        self.VERSION_ORDER = VERSION_ORDER
        self.VERSION_INDEX = VERSION_INDEX

    def get(self, now):
        auth = self.auth
        db = self.db
        VERSION_ORDER = self.VERSION_ORDER
        VERSION_INDEX = self.VERSION_INDEX

        myId = None
        if auth.user:
            myId = auth.user.id
        labelInfo = collections.defaultdict(lambda: {})

        def titleBadge(lid, ltype, publ, good, num, tot):
            name = labelInfo[ltype][lid] if ltype is not None else "Shared Queries"
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
                if myId is not None:
                    if lid:
                        rename = f'<a class="r_{ltype}" lid="{lid}" href="#"></a>'
                    select = f'<a class="s_{ltype} fa fa-lg" lid="{lid}" href="#"></a>'
                else:
                    if lid:
                        rename = f'<a class="v_{ltype}" lid="{lid}" href="#"></a>'
            return f"""{select}
<span n="1">{hEsc(name)}</span><span class="brq">({badge})</span> {rename}"""

        condition = (
            """
where query.is_shared = 'T'
"""
            if myId is None
            else f"""
where query.is_shared = 'T' or query.created_by = {myId}
"""
        )

        projectQueryXSql = f"""
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

        projectQuerySql = f"""
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

        projectQuery = db.executesql(projectQuerySql)
        projectQueryX = db.executesql(projectQueryXSql)
        projectQueries = collections.OrderedDict()
        for (
            queryId,
            orgName,
            orgId,
            projectName,
            projectId,
            userName,
            userId,
            queryName,
            queryShared,
        ) in projectQuery:
            qSharedStatus = queryShared == "T"
            qOwnStatus = userId == myId
            projectQueries[queryId] = {
                "": (
                    orgName,
                    orgId,
                    projectName,
                    projectId,
                    userName,
                    userId,
                    queryName,
                    qSharedStatus,
                    qOwnStatus,
                ),
                "publ": False,
                "good": False,
                "v": [4 for v in VERSION_ORDER],
            }
        for (
            queryId,
            vr,
            queryIsPub,
            queryPubOn,
            queryModOn,
            queryExeOn,
        ) in projectQueryX:
            queryInfo = projectQueries[queryId]
            queryExeStatus = None
            if queryExeOn:
                queryExeStatus = queryExeOn >= queryModOn
            queryPubStatus = (
                False
                if queryIsPub != "T"
                else None
                if queryPubOn > now - PUBLISH_FREEZE
                else True
            )
            queryStatus = (
                1
                if queryPubStatus
                else 2
                if queryPubStatus is None
                else 3
                if queryExeStatus
                else 4
                if queryExeStatus is None
                else 5
            )
            queryInfo["v"][VERSION_INDEX[vr]] = queryStatus
            if queryPubStatus or queryPubStatus is None:
                queryInfo["publ"] = True
            if queryExeStatus:
                queryInfo["good"] = True

        projectOrgSql = """
select name, id from organization order by name
;
"""
        porg = db.executesql(projectOrgSql)

        projectSql = """
select name, id from project order by name
;
"""
        project = db.executesql(projectSql)

        tree = collections.OrderedDict()
        countSet = collections.defaultdict(lambda: set())
        countOrg = collections.defaultdict(lambda: 0)
        countOrgPub = collections.defaultdict(lambda: 0)
        countOrgGood = collections.defaultdict(lambda: 0)
        countOrgTotal = collections.defaultdict(lambda: 0)
        countProject = collections.defaultdict(
            lambda: collections.defaultdict(lambda: 0)
        )
        countProjectPub = collections.defaultdict(
            lambda: collections.defaultdict(lambda: 0)
        )
        countProjectGood = collections.defaultdict(
            lambda: collections.defaultdict(lambda: 0)
        )
        countProjectTotal = collections.defaultdict(lambda: 0)
        countUser = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countUserPub = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countUserGood = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        )
        countUserTotal = collections.defaultdict(lambda: 0)
        count = 0
        countPub = 0
        countGood = 0
        for queryId in projectQueries:
            projectQueryInfo = projectQueries[queryId]
            (
                orgName,
                orgId,
                projectName,
                projectId,
                userName,
                userId,
                queryName,
                queryShared,
                queryOwn,
            ) = projectQueryInfo[""]
            queryPub = projectQueryInfo["publ"]
            queryGood = projectQueryInfo["good"]
            countSet["o"].add(orgId)
            countSet["p"].add(projectId)
            countSet["u"].add(userId)
            countSet["q"].add(queryId)
            labelInfo["o"][orgId] = orgName
            labelInfo["p"][projectId] = projectName
            labelInfo["u"][userId] = userName
            if queryOwn:
                countSet["m"].add(queryId)
            if not queryShared:
                countSet["r"].add(queryId)
            if queryPub:
                countUserPub[orgId][projectId][userId] += 1
                countProjectPub[orgId][projectId] += 1
                countOrgPub[orgId] += 1
                countPub += 1
            if queryGood:
                countUserGood[orgId][projectId][userId] += 1
                countProjectGood[orgId][projectId] += 1
                countOrgGood[orgId] += 1
                countGood += 1
            tree.setdefault(orgId, collections.OrderedDict()).setdefault(
                projectId, collections.OrderedDict()
            ).setdefault(userId, []).append(queryId)
            count += 1
            countOrg[orgId] += 1
            countProject[orgId][projectId] += 1
            countUser[orgId][projectId][userId] += 1
            countOrgTotal[orgId] += 1
            countProjectTotal[projectId] += 1
            countUserTotal[userId] += 1

        labelInfo["o"][0] = "Projects without Queries"
        labelInfo["p"][0] = "New Project"
        labelInfo["u"][0] = ""
        labelInfo["q"] = projectQueries
        countOrg[0] = 0
        countProject[0][0] = 0
        for (orgName, orgId) in porg:
            if orgId in labelInfo["o"]:
                continue
            countSet["o"].add(orgId)
            labelInfo["o"][orgId] = orgName
            tree[orgId] = collections.OrderedDict()

        for (projectName, projectId) in project:
            if projectId in labelInfo["p"]:
                continue
            countSet["o"].add(0)
            countSet["p"].add(projectId)
            labelInfo["p"][projectId] = projectName
            tree.setdefault(0, collections.OrderedDict())[
                projectId
            ] = collections.OrderedDict()

        categoryCount = dict((x[0], len(x[1])) for x in countSet.items())
        categoryCount["userId"] = myId
        title = titleBadge(None, None, countPub, countGood, count, count)
        dest = [dict(title=str(title), folder=True, children=[], data=categoryCount)]
        curDest = dest[-1]["children"]
        curSource = tree
        for orgId in curSource:
            orgN = countOrg[orgId]
            orgPub = countOrgPub[orgId]
            orgGood = countOrgGood[orgId]
            orgTot = countOrgTotal[orgId]
            orgTitle = titleBadge(orgId, "o", orgPub, orgGood, orgN, orgTot)
            curDest.append(dict(title=str(orgTitle), folder=True, children=[]))
            curOrgDest = curDest[-1]["children"]
            curOrgSource = curSource[orgId]
            for projectId in curOrgSource:
                projectN = countProject[orgId][projectId]
                projectPub = countProjectPub[orgId][projectId]
                projectPub = countProjectGood[orgId][projectId]
                projectTot = countProjectTotal[projectId]
                projectTitle = titleBadge(
                    projectId, "p", projectPub, projectPub, projectN, projectTot
                )
                curOrgDest.append(
                    dict(title=str(projectTitle), folder=True, children=[])
                )
                curProjectDest = curOrgDest[-1]["children"]
                curProjectSource = curOrgSource[projectId]
                for userId in curProjectSource:
                    userN = countUser[orgId][projectId][userId]
                    userPub = countUserPub[orgId][projectId][userId]
                    userGood = countUserGood[orgId][projectId][userId]
                    userTot = countUserTotal[userId]
                    userTitle = titleBadge(
                        userId, "u", userPub, userGood, userN, userTot
                    )
                    curProjectDest.append(
                        dict(title=str(userTitle), folder=True, children=[])
                    )
                    curUserDest = curProjectDest[-1]["children"]
                    curUserSource = curProjectSource[userId]
                    for queryId in curUserSource:
                        projectQueryInfo = labelInfo["q"][queryId]
                        (
                            orgName,
                            orgId,
                            projectName,
                            projectId,
                            userName,
                            userId,
                            queryName,
                            queryShared,
                            queryOwn,
                        ) = projectQueryInfo[""]
                        queryPub = projectQueryInfo["publ"]
                        queryGood = projectQueryInfo["good"]
                        queryVersions = projectQueryInfo["v"]
                        queryOwnRep = "r" if queryOwn else "v"
                        queryMyRep = ("qmy" if queryOwn else "",)
                        querySharedRep = "" if queryShared else "qpriv"
                        queryIdRep = (iEncode("q", queryId),)
                        rename = f"""<a
class="{queryOwnRep}_q" lid="{queryIdRep}" href="#"></a>"""
                        versionRep = " ".join(
                            formatVersion(
                                "q", queryId, v, queryVersions[VERSION_INDEX[v]]
                            )
                            for v in VERSION_ORDER
                        )
                        curUserDest.append(
                            dict(
                                title=f"""{versionRep} <a
class="q {queryMyRep} {querySharedRep}"
n="1" qid="{queryId}" href="#">{hEsc(queryName)}</a>
<a class="md" href="#"></a> {rename}""",
                                key=f"q{queryId}",
                                folder=False,
                            )
                        )
        return dict(data=json.dumps(dest))
