#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 DANS-KNAW
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# #######################################################################
# Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
if 0:
    from . import *
# End of fake imports to satisfy the editor.
# #######################################################################

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

# long import statement for editor and web2py
# from applications.shebanq.modules import clamdros
# short import statement only satisfies web2py
#import trypy as tpy

#only use this during development:
# reload(clamdros)

from gluon.custom_import import track_changes; track_changes(True)

import json
from itertools import groupby

from render import Verses, Viewsettings

def getpassage(no_controller=True):
    book_name = request.vars.book or None
    chapter_num = request.vars.chapter or None
    book = None
    chapter = None
    if book_name:
        book = passage_db.book(name=book_name)
    if chapter_num != None and book:
        chapter = passage_db.chapter(chapter_num=chapter_num, book_id=book.id)
    return (book, chapter)

def group_MySQL(input):
    """ HELPER for query_form
    Reorganise a query_monad query.

    Input (query dict):
    [
        {'query_id': 10L, 'first_m': 1L,  'last_m': 7L},
        {'query_id': 7L,  'first_m': 1L,  'last_m': 7L},
        {'query_id': 9L,  'first_m': 1L,  'last_m': 7L},
        {'query_id': 10L, 'first_m': 10L, 'last_m': 13L},
        {'query_id': 5L,  'first_m': 1L,  'last_m': 7L}
    ]
    Output (replace the query id with the actual query row object):
    [
        {'query': <Row {'query': 'Dit is query 5.', 'id': 5L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 7.', 'id': 7L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 9.', 'id': 9L, ...}>,
         'monadsets': [(1L, 7L),],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L]',},
        {'query': <Row {'query': 'Dit is query 10.', 'id': 10L, ...}>,
         'monadsets': [(1L, 7L), (10L, 15L)],
         'json_monads': '[1L, 2L, 3L, 4L, 5L, 6L, 7L, 10L, 11L, 12L, 13L]',},
    ]
    """
    sorted_input = sorted(input, key=lambda x: x['query_id'])
    groups = groupby(sorted_input, key=lambda x: x['query_id'])
    r = []
    for k, v in groups:
        query = db.queries(k)
        monads = [(m['first_m'], m['last_m']) for m in v]
        json_monads = json.dumps(sorted(list(set(sum([range(x[0], x[1] + 1) for x in monads], [])))))
        r.append({'item': query, 'monads': json_monads})
    return r


def get_monadsets_MySQL(chapter):
    """ HELPER to get all monadsets that relate to selected chapter.
    These will be transformed into queries with monads by 'group'.

    Output:
    [{'first_m': 296211L, 'query_id': 2L, 'last_m': 296496L},
     {'first_m': 296438L, 'query_id': 6L, 'last_m': 296438L},
     {'first_m': 296470L, 'query_id': 6L, 'last_m': 296470L},
     {'first_m': 296494L, 'query_id': 6L, 'last_m': 296494L}, ...]
    """
    return db.executesql('''
select DISTINCT
    query_id,
    GREATEST(first_m, {chapter_first_m}) as first_m,
    LEAST(last_m, {chapter_last_m}) as last_m
from
    monadsets inner join queries on
    monadsets.query_id = queries.id and queries.is_published = 'T' and queries.executed_on >= queries.modified_on
where
    (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
    ({chapter_first_m} BETWEEN first_m AND last_m);
'''.format(
         chapter_last_m=chapter.last_m,
         chapter_first_m=chapter.first_m,
    ), as_dict=True)

def get_lexemes(chapter):
    lexeme_data = db.executesql('''
select
    anchor, lexicon_id
from
    word_verse
where
    anchor BETWEEN {chapter_first_m} AND {chapter_last_m}
'''.format(
         chapter_last_m=chapter.last_m,
         chapter_first_m=chapter.first_m,
    ))
    grouped = collections.defaultdict(lambda: [])
    for lex in lexeme_data:
        grouped[x[1]].append(x[0])
    r = []
    for lex_id in grouped:
        lexeme = passage_db.lexicon(lex_id)
        r.append({'item': lexeme, 'monads': json.dumps(grouped[lex_id])})
    return r

def sideq(): return side_list('q')
def sidew(): return side_list('w')

def side_list(k):
    (book, chapter) = getpassage()
    if k == 'q':
        monadsets = get_monadsets_MySQL(chapter)
        side_items = group_MySQL(monadsets)
    else:
        side_items = get_lexemes(chapter)
    return dict(
        viewsettings=Viewsettings('passage'),
        side_items=side_items,
    )

def verses():
    (book, chapter) = getpassage()
    verses = None
    if chapter: verses = Verses(passage_db, 'passage', chapter=chapter.id)

    if verses != None:
        response.subtitle = "{} {}".format(book.name, chapter.chapter_num)

    result = dict(
        page_kind='passage',
        book=book.name if book != None else None,
        chapter=chapter.chapter_num if chapter != None else None,
        verses=verses,
    )
    return result

def passage(): return skeleton('passage')

def skeleton(kind):
    books_data = passage_db.executesql('''
select name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id;
    ''')


#    return passage_db().select(passage_db.book.ALL,
#                               cache=(cache.ram, 3600),
#                               cacheable=True)

    books_order = [x[0] for x in books_data]
    books = dict(x for x in books_data)
    viewsettings = Viewsettings(kind)
    return dict(
        viewsettings=viewsettings,
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
    )

def index():
    """
    example action using the internationalization operator T 
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    response.title = T("SHEBANQ")
    response.subtitle = T("Query the Hebrew Bible through the ETCBC4 database")
    return dict()

def about():
    response.title = T("SHEBANQ")
    response.subtitle = T("About the ETCBC4 database")
    return dict()

def help():
    response.title = T("SHEBANQ")
    response.subtitle = T("Help for using SHEBANQ")
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


