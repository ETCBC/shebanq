#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)
import datetime
import rss2

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
            cover_image=feed.get('cover_image', None),
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

# see controller hebrew.py for more info about the next query. Look for pqueryx_sql

    pqueryx_sql = u'''
select
    query.id as qid,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    query.name as qname,
    query.description as qdesc,
    qe.executed_on as qexe,
    qe.version as qver
from query inner join
    (
        select t1.query_id, t1.executed_on, t1.version
        from query_exe t1
          left outer join query_exe t2
            on (
                t1.query_id = t2.query_id and 
                t1.executed_on < t2.executed_on and
                t2.executed_on >= t2.modified_on
            )
        where
            (t1.executed_on is not null and t1.executed_on >= t1.modified_on) and
            t2.query_id is null
    ) as qe
on qe.query_id = query.id
inner join auth_user on query.created_by = auth_user.id
where query.is_shared = 'T'
order by qe.executed_on desc, auth_user.last_name
'''

    pqueryx = db.executesql(pqueryx_sql)
    pqueries = []
    for (qid, ufname, ulname, qname, qdesc, qexe, qver) in pqueryx:
        title = u'{} {}: {}'.format(ufname, ulname, qname)
        description = qdesc
        link = URL('hebrew', 'query', vars=dict(id=qid, version=qver), host=True, extension='')
        pqueries.append(dict(title=title, link=link, description=description, created_on=qexe))

    return dict(
        title="SHEBANQ queries",
        link=URL('rss', 'feed', host=True, extension='rss'),
        image=(
            URL('static', 'images/shebanq_logo_small.png', host=True),
            'SHEBANQ queries',
            URL('rss', 'feed', host=True, extension='rss'),
        ),
        cover_image= URL('static', 'images/shebanq_logo.png', host=True),
        description="The shared queries in SHEBANQ",
        created_on=request.utcnow,
        entries=pqueries,
        rss=rss,
    )


