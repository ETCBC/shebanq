#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from gluon.custom_import import track_changes; track_changes(True)
from datetime import datetime
from markdown import markdown

def isodt(dt=None): return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") if dt==None else dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# here is a bit that replaces the same functions in gluon/serializers.py
# The gluon version eventually leads to UNICODE errors

def atom(queries):
    icon_image = URL('static', 'images/shebanq_logo_small.png', host=True),
    logo_image = URL('static', 'images/shebanq_logo_.png', host=True),
    cover_image = URL('static', 'images/shebanq_cover.png', host=True),
    now = datetime.utcnow()
    xml = []
    xml.append(u'''<?xml version="1.0" encoding="utf-8"?>
''')
    xml.append(u'''
<feed xmlns="http://www.w3.org/2005/Atom">
        version='1.0',
        xmlns:atom='http://www.w3.org/2005/Atom',
        xmlns:webfeeds='http://webfeeds.org/rss/1.0',
>''')
    xml.append(u'''
    <title>SHEBANQ</title>
    <subtitle>Shared queries, recently executed</subtitle>
    <link href="{}" rel="self"/>
    <link href="{}"/>
    <updated>{}</updated>
'''.format(
    URL('rss', 'feed', host=True, extension='rss'),
    URL('', '', host=True, extension=''),
    isodt(),
))

    for (author, title, description, updated, source) in queries:
        xml.append(u'''
    <entry>
        <title>{}</title>
        <link href="{}"/>
        <updated>{}</updated>
        <content type="html">{}</content>
        <author><name>{}</name></author>
    </entry>
'''.format(
    title,
    source,
    updated,
    markdown(description),
    author,
))
    xml.append(u'''
</feed>
''')
    return u''.join(xml)


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
        author = u'{} {}'.format(ufname, ulname)
        title = qname
        description = qdesc
        source = URL('hebrew', 'query', vars=dict(id=qid, version=qver), host=True, extension='')
        pqueries.append((
            author,
            title,
            description,
            isodt(dt=qexe),
            source,
        ))

    return dict(xml=atom(pqueries))
