from textwrap import dedent
import collections
import json

from gluon import current

from constants import PUBLISH_FREEZE
from helpers import hEsc, iEncode, formatVersion


class QUERYTREE:
    def __init__(self):
        pass

    def get(self):
        """Get the metadata of all queries and deliver it as JSON.
        """

        auth = current.auth
        db = current.db
        VERSION_ORDER = current.VERSION_ORDER
        VERSION_INDEX = current.VERSION_INDEX

        myId = None
        if auth.user:
            myId = auth.user.id
        objInfo = collections.defaultdict(lambda: {})

        def titleBadge(obj_id, objType, publ, good, num, tot):
            name = objInfo[objType][obj_id] if objType is not None else "Shared Queries"
            nums = []
            if publ != 0:
                nums.append(f'<span class="special fa fa-quote-right"> {publ}</span>')
            if good != 0:
                nums.append(f'<span class="good fa fa-gears"> {good}</span>')
            badge = ""
            if len(nums) == 0:
                if tot == num:
                    badge = f'<span class="total">{tot}</span>'
                else:
                    badge = f'{num} of <span class="total">{tot}</span>'
            else:
                nRep = ", ".join(nums)
                if tot == num:
                    badge = f'{nRep} of <span class="total">{tot}</span>'
                else:
                    badge = f'{nRep} of {num} of all <span class="total">{tot}</span>'
            rename = ""
            select = ""
            if objType in {"o", "p"}:
                if myId is not None:
                    if obj_id:
                        rename = (
                            f'<a class="r_{objType}" obj_id="{obj_id}" href="#"></a>'
                        )
                    select = dedent(
                        f"""<a
                            class="s_{objType} fa fa-lg"
                            obj_id="{obj_id}"
                            href="#"></a>"""
                    )
                else:
                    if obj_id:
                        rename = (
                            f'<a class="v_{objType}" obj_id="{obj_id}" href="#"></a>'
                        )
            return dedent(
                f"""{select}
                <span n="1">{hEsc(name)}</span><span
                class="brq">({badge})</span> {rename}"""
            )

        condition = (
            dedent(
                """
                where query.is_shared = 'T'
                """
            )
            if myId is None
            else dedent(
                f"""
                where query.is_shared = 'T' or query.created_by = {myId}
            """
            )
        )

        projectQueryXSql = dedent(
            f"""
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
        )

        projectQuerySql = dedent(
            f"""
            select
                query.id as query_id,
                organization.name as org_name, organization.id as org_id,
                project.name as project_name, project.id as project_id,
                concat(auth_user.first_name, ' ', auth_user.last_name) as uname,
                auth_user.id as user_id,
                query.name as query_name, query.is_shared as is_shared
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
        )

        projectQuery = db.executesql(projectQuerySql)
        projectQueryX = db.executesql(projectQueryXSql)
        projectQueries = collections.OrderedDict()
        for (
            query_id,
            orgName,
            org_id,
            projectName,
            project_id,
            userName,
            user_id,
            queryName,
            queryShared,
        ) in projectQuery:
            qSharedStatus = queryShared == "T"
            qOwnStatus = user_id == myId
            projectQueries[query_id] = {
                "": (
                    orgName,
                    org_id,
                    projectName,
                    project_id,
                    userName,
                    user_id,
                    queryName,
                    qSharedStatus,
                    qOwnStatus,
                ),
                "publ": False,
                "good": False,
                "v": [4 for v in VERSION_ORDER],
            }

        now = current.request.utcnow

        for (
            query_id,
            vr,
            queryIs_published,
            queryPublished_on,
            queryMod_on,
            queryExe_on,
        ) in projectQueryX:
            queryInfo = projectQueries[query_id]
            queryExeStatus = None
            if queryExe_on:
                queryExeStatus = queryExe_on >= queryMod_on
            queryPubStatus = (
                False
                if queryIs_published != "T"
                else None
                if queryPublished_on > now - PUBLISH_FREEZE
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

        projectOrgSql = dedent(
            """
            select name, id from organization order by name
            ;
            """
        )
        porg = db.executesql(projectOrgSql)

        projectSql = dedent(
            """
            select name, id from project order by name
            ;
            """
        )
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
        for query_id in projectQueries:
            projectQueryInfo = projectQueries[query_id]
            (
                orgName,
                org_id,
                projectName,
                project_id,
                userName,
                user_id,
                queryName,
                queryShared,
                queryOwn,
            ) = projectQueryInfo[""]
            queryPub = projectQueryInfo["publ"]
            queryGood = projectQueryInfo["good"]
            countSet["o"].add(org_id)
            countSet["p"].add(project_id)
            countSet["u"].add(user_id)
            countSet["q"].add(query_id)
            objInfo["o"][org_id] = orgName
            objInfo["p"][project_id] = projectName
            objInfo["u"][user_id] = userName
            if queryOwn:
                countSet["m"].add(query_id)
            if not queryShared:
                countSet["r"].add(query_id)
            if queryPub:
                countUserPub[org_id][project_id][user_id] += 1
                countProjectPub[org_id][project_id] += 1
                countOrgPub[org_id] += 1
                countPub += 1
            if queryGood:
                countUserGood[org_id][project_id][user_id] += 1
                countProjectGood[org_id][project_id] += 1
                countOrgGood[org_id] += 1
                countGood += 1
            tree.setdefault(org_id, collections.OrderedDict()).setdefault(
                project_id, collections.OrderedDict()
            ).setdefault(user_id, []).append(query_id)
            count += 1
            countOrg[org_id] += 1
            countProject[org_id][project_id] += 1
            countUser[org_id][project_id][user_id] += 1
            countOrgTotal[org_id] += 1
            countProjectTotal[project_id] += 1
            countUserTotal[user_id] += 1

        objInfo["o"][0] = "Projects without Queries"
        objInfo["p"][0] = "New Project"
        objInfo["u"][0] = ""
        objInfo["q"] = projectQueries
        countOrg[0] = 0
        countProject[0][0] = 0
        for (orgName, org_id) in porg:
            if org_id in objInfo["o"]:
                continue
            countSet["o"].add(org_id)
            objInfo["o"][org_id] = orgName
            tree[org_id] = collections.OrderedDict()

        for (projectName, project_id) in project:
            if project_id in objInfo["p"]:
                continue
            countSet["o"].add(0)
            countSet["p"].add(project_id)
            objInfo["p"][project_id] = projectName
            tree.setdefault(0, collections.OrderedDict())[
                project_id
            ] = collections.OrderedDict()

        categoryCount = dict((x[0], len(x[1])) for x in countSet.items())
        categoryCount["user_id"] = myId
        title = titleBadge(None, None, countPub, countGood, count, count)
        dest = [dict(title=str(title), folder=True, children=[], data=categoryCount)]
        curDest = dest[-1]["children"]
        curSource = tree
        for org_id in curSource:
            orgN = countOrg[org_id]
            orgPub = countOrgPub[org_id]
            orgGood = countOrgGood[org_id]
            orgTot = countOrgTotal[org_id]
            orgTitle = titleBadge(org_id, "o", orgPub, orgGood, orgN, orgTot)
            curDest.append(dict(title=str(orgTitle), folder=True, children=[]))
            curOrgDest = curDest[-1]["children"]
            curOrgSource = curSource[org_id]
            for project_id in curOrgSource:
                projectN = countProject[org_id][project_id]
                projectPub = countProjectPub[org_id][project_id]
                projectPub = countProjectGood[org_id][project_id]
                projectTot = countProjectTotal[project_id]
                projectTitle = titleBadge(
                    project_id, "p", projectPub, projectPub, projectN, projectTot
                )
                curOrgDest.append(
                    dict(title=str(projectTitle), folder=True, children=[])
                )
                curProjectDest = curOrgDest[-1]["children"]
                curProjectSource = curOrgSource[project_id]
                for user_id in curProjectSource:
                    userN = countUser[org_id][project_id][user_id]
                    userPub = countUserPub[org_id][project_id][user_id]
                    userGood = countUserGood[org_id][project_id][user_id]
                    userTot = countUserTotal[user_id]
                    userTitle = titleBadge(
                        user_id, "u", userPub, userGood, userN, userTot
                    )
                    curProjectDest.append(
                        dict(title=str(userTitle), folder=True, children=[])
                    )
                    curUserDest = curProjectDest[-1]["children"]
                    curUserSource = curProjectSource[user_id]
                    for query_id in curUserSource:
                        projectQueryInfo = objInfo["q"][query_id]
                        (
                            orgName,
                            org_id,
                            projectName,
                            project_id,
                            userName,
                            user_id,
                            queryName,
                            queryShared,
                            queryOwn,
                        ) = projectQueryInfo[""]
                        queryPub = projectQueryInfo["publ"]
                        queryGood = projectQueryInfo["good"]
                        queryVersions = projectQueryInfo["v"]
                        queryOwnRep = "r" if queryOwn else "v"
                        queryMyRep = "qmy" if queryOwn else ""
                        querySharedRep = "" if queryShared else "qpriv"
                        queryIdRep = iEncode("q", query_id)
                        rename = dedent(
                            f"""<a
                            class="{queryOwnRep}_q"
                            obj_id="{queryIdRep}"
                            href="#"></a>"""
                        )
                        versionRep = " ".join(
                            formatVersion(
                                "q", query_id, v, queryVersions[VERSION_INDEX[v]]
                            )
                            for v in VERSION_ORDER
                        )
                        curUserDest.append(
                            dict(
                                title=dedent(
                                    f"""{versionRep} <a
                                    class="q {queryMyRep} {querySharedRep}"
                                    n="1"
                                    query_id="{query_id}"
                                    href="#">{hEsc(queryName)}</a>
                                    <a class="md" href="#"></a> {rename}"""
                                ),
                                key=f"q{query_id}",
                                folder=False,
                            )
                        )
        return dict(data=json.dumps(dest))
