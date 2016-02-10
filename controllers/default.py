#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes; track_changes(True)

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

from codecs import encode

def rss():
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
        title = encode(u'{} {}: {}'.format(ufname, ulname, qname), 'utf-8')
        description = encode(qdesc, 'utf-8')
        link = URL('hebrew', 'query', vars=dict(id=qid), host=True, extension='')
        pqueries.append(dict(title=title, link=link, description=description, created_on=qexe))

    return dict(
        title="SHEBANQ queries",
        link=URL('rss', host=True),
        description="The shared queries in SHEBANQ",
        created_on=request.now,
        entries=pqueries,
    )


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

