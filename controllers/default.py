#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from gluon.custom_import import track_changes; track_changes(True)
from datetime import datetime
from markdown import markdown
from render import h_esc


EXPIRE = 3600*24*30

#def myerror(): return 1/0

def index():
    session.forget(response)
    response.title = T("SHEBANQ")
    response.subtitle = T("Query the Hebrew Bible through the ETCBC4 database")
    return dict()

def help():
    session.forget(response)
    response.title = T("SHEBANQ - help")
    response.subtitle = T("Help for using SHEBANQ")
    return dict()

def sources():
    session.forget(response)
    response.title = T("SHEBANQ - sources")
    response.subtitle = T("Sources for recreating SHEBANQ")
    return dict()

def news():
    session.forget(response)
    response.title = T("SHEBANQ - news")
    response.subtitle = T("Release notes of SHEBANQ")
    return dict()

def restapi():
    session.forget(response)
    response.title = T("SHEBANQ - rest api")
    response.subtitle = T("REST API (for integrators)")
    return dict()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """

    response.title = T("User Profile")
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())

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
<feed
        xmlns="http://www.w3.org/2005/Atom"
        version="1.0"
        xmlns:atom="http://www.w3.org/2005/Atom"
        xmlns:webfeeds="http://webfeeds.org/rss/1.0"
>''')
    xml.append(u'''
    <title>SHEBANQ</title>
    <subtitle>Shared queries, recently executed</subtitle>
    <link href="{}" rel="self"/>
    <link href="{}"/>
    <id>{}</id>
    <updated>{}</updated>
'''.format(
    h_esc(URL('rss', 'feed', host=True, extension='rss')),
    h_esc(URL('', '', host=True, extension='')),
    h_esc(URL('hebrew', 'queries', host=True, extension='')), 
    isodt(),
))

    for (eid, author, title, description, updated, source) in queries:
        xml.append(u'''
    <entry>
        <title>{}</title>
        <link href="{}"/>
        <id>{}</id>
        <updated>{}</updated>
        <content type="html">{}</content>
        <author><name>{}</name></author>
    </entry>
'''.format(
    h_esc(title),
    h_esc(source),
    eid,
    updated,
    markdown(description),
    h_esc(author),
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
    for (qid, ufname, ulname, qname, qdesc, qvid, qexe, qver) in pqueryx:
        author = u'{} {}'.format(ufname, ulname)
        title = qname
        description = qdesc
        source = URL('hebrew', 'query', vars=dict(id=qid, version=qver), host=True, extension='')
        pqueries.append((
            '{}-{}-{}'.format('shebanq', qid, qvid),
            author,
            title,
            description,
            isodt(dt=qexe),
            source,
        ))

    return dict(xml=atom(pqueries))
