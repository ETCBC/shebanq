#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import gluon.contrib.rss2 as rss2

# here is a bit that replaces the same functions in gluon/serializers.py
# The gluon version eventually leads to UNICODE errors

def safe_encode(text):
    if not isinstance(text, (str, unicode)):
        text = str(text)
    return text

def rss(feed):
    if not 'entries' in feed and 'items' in feed:
        feed['entries'] = feed['items']

    def safestr(obj, key, default=''):
        return safe_encode(obj.get(key,''))

    now = datetime.datetime.utcnow()
    rss = rss2.RSS2(
        title=safestr(feed,'title'),
            image=rss2.Image(*feed.get('image', None)),
            link=safestr(feed,'link'),
            description=safestr(feed,'description'),
            lastBuildDate=feed.get('created_on', now),
            items=[
                rss2.RSSItem(
                    title=safestr(entry,'title','(notitle)'),
                    link=safestr(entry,'link'),
                    description=safestr(entry,'description'),
                    pubDate=entry.get('created_on', now)
                ) for entry in feed.get('entries', [])
            ])
    return rss.to_xml(encoding='utf-8')


def feed():
    session.forget(response)

    pqueryx_sql = u'''
select
query.id as qid,
auth_user.first_name as ufname,
auth_user.last_name as ulname,
query.name as qname,
query.description as qdesc,
max(query_exe.executed_on) as qexe
from query_exe
inner join query on query.id = query_exe.query_id
inner join auth_user on query.created_by = auth_user.id
where (query.is_shared = 'T')
and (query_exe.executed_on is not null and query_exe.executed_on > query_exe.modified_on)
group by query.id
order by query_exe.executed_on desc, auth_user.last_name
'''

    pqueryx = db.executesql(pqueryx_sql)
    pqueries = []
    for (qid, ufname, ulname, qname, qdesc, qexe) in pqueryx:
        title = u'{} {}: {}'.format(ufname, ulname, qname)
        description = qdesc
        link = URL('hebrew', 'query', vars=dict(id=qid), host=True, extension='')
        pqueries.append(dict(title=title, link=link, description=description, created_on=qexe))

    return dict(
        title="SHEBANQ queries",
        link=URL('rss', 'feed', host=True, extension='rss'),
        image=(
            URL('static', 'images/shebanq_logo.png', host=True),
            'SHEBANQ queries',
            URL('rss', 'feed', host=True, extension='rss'),
        ),
        description="The shared queries in SHEBANQ",
        created_on=request.utcnow,
        entries=pqueries,
        rss=rss,
    )


