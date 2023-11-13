from textwrap import dedent
import json

from gluon import current

from helpers import hEsc


RECENT_LIMIT = 50


class QUERYRECENT:
    """Handles the set of recent queries.

    It can select the most recently saved shared queries.

    It can export them as an RSS feed.
    """

    def __init__(self):
        pass

    def recent(self):
        """Select the most recently saved shared queries.

        The next query contains a clever idea from
        [stackoverflow](https://stackoverflow.com/questions/5657446/mysql-query-max-group-by).

        We want to find the most recent MQL queries.
        Queries may have multiple executions.
        We want to have the queries with the most recent executions.

        From such queries, we only want to have the single most recent execution.

        This idea can be obtained by left outer joining the `query_exe` table
        with itself (`qe1` with `qe2`) on the condition that
        those rows are combined
        where `qe1` and `qe2` belong to the same query, and `qe2` is more recent.
        Rows in the combined table where `qe2` is null,
        are such that `qe1` is most recent.

        This is the basic idea.

        We then have to refine it: we only want shared queries.
        That is an easy where condition on the final result.
        We only want to have up-to-date queries.
        So the join condition is not that `qe2` is more recent,
        but that `qe2` is up-to-date and more recent.
        And we need to add a where to express that `qe1` is up to date.
        """

        db = current.db

        projectQueryXSql = dedent(
            f"""
            select
                query.id as query_id,
                auth_user.first_name,
                auth_user.last_name,
                query.name as query_name,
                qe.executed_on as qexe,
                qe.version as qver
            from query inner join
                (
                    select qe1.query_id, qe1.executed_on, qe1.version
                    from query_exe qe1
                      left outer join query_exe qe2
                        on (
                            qe1.query_id = qe2.query_id and
                            qe1.executed_on < qe2.executed_on and
                            qe2.executed_on >= qe2.modified_on
                        )
                    where
                        (
                            qe1.executed_on is not null and
                            qe1.executed_on >= qe1.modified_on
                        ) and
                        qe2.query_id is null
                ) as qe
            on qe.query_id = query.id
            inner join auth_user on query.created_by = auth_user.id
            where query.is_shared = 'T'
            order by qe.executed_on desc, auth_user.last_name
            limit {RECENT_LIMIT};
            """
        )

        pqueryx = db.executesql(projectQueryXSql)
        pqueries = []
        for (query_id, first_name, last_name, query_name, qexe, qver) in pqueryx:
            text = hEsc(f"{first_name[0]} {last_name[0:9]}: {query_name[0:20]}")
            title = hEsc(f"{first_name} {last_name}: {query_name}")
            pqueries.append(dict(id=query_id, text=text, title=title, version=qver))

        return dict(data=json.dumps(dict(queries=pqueries, msgs=[], good=True)))

    def feed(self):
        db = current.db

        sql = dedent(
            """
            select
                query.id as query_id,
                auth_user.first_name,
                auth_user.last_name,
                query.name as query_name,
                query.description,
                qe.id as qvid,
                qe.executed_on as qexe,
                qe.version as qver
            from query inner join
                (
                    select t1.id, t1.query_id, t1.executed_on, t1.version
                    from query_exe t1
                      left outer join query_exe t2
                        on (
                            t1.query_id = t2.query_id and
                            t1.executed_on < t2.executed_on and
                            t2.executed_on >= t2.modified_on
                        )
                    where
                        (
                            t1.executed_on is not null and
                            t1.executed_on >= t1.modified_on
                        ) and
                        t2.query_id is null
                ) as qe
            on qe.query_id = query.id
            inner join auth_user on query.created_by = auth_user.id
            where query.is_shared = 'T'
            order by qe.executed_on desc, auth_user.last_name
            """
        )

        return db.executesql(sql)
