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
        json_monads = json.dumps(sorted(list(set(sum([range(x[0], x[1] + 1)
                                                      for x in monads],
                                                     [])))))
        r.append({'query': query, 'json_monads': json_monads})
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
    return db.executesql("""
           select DISTINCT query_id,
                           GREATEST(first_m, {chapter_first_m}) as first_m,
                           LEAST(last_m, {chapter_last_m}) as last_m
           from monadsets inner join queries on
            monadsets.query_id = queries.id and
            queries.is_published = 'T' and
            queries.executed_on >= queries.modified_on
           WHERE (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
                 (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
                 ({chapter_first_m} BETWEEN first_m AND last_m);""".format(chapter_last_m=chapter.last_m,
                                                                           chapter_first_m=chapter.first_m),
                         as_dict=True)


def query_form(): return query_form_generic()

def query_form_generic(viewsettings=None):
    (book, chapter) = getpassage()
    monadsets = get_monadsets_MySQL(chapter)
    query_monads = group_MySQL(monadsets)
    if viewsettings == None: viewsettings = Viewsettings('passage')
    return dict(
        query_monads=query_monads,
        viewsettings=viewsettings
    )

def chapter_form():
    (book, chapter) = getpassage()
    verses = None
    if chapter: verses = Verses(passage_db, 'passage', chapter=chapter.id)

    viewsettings = Viewsettings('passage')
    queries = query_form_generic(viewsettings=viewsettings) if viewsettings.state['hlview']['q']['get'] and chapter else dict(query_monads=[], viewsettings=viewsettings)
    if verses != None:
        response.subtitle = "{} {}".format(book.name, chapter.chapter_num)

    word_monads = [
        {
            'word': {
                'id': 1,
                'entry': 'aap',
                'gloss': 'AAP',
            },
            'json_monads': '[1, 3, 5, 7]',
        },
        {
            'word': {
                'id': 2,
                'entry': 'noot',
                'gloss': 'NOOT',
            },
            'json_monads': '[2, 4, 6, 8]',
        },
    ]

    result = dict((
        ('word_monads', word_monads),
        ('page_kind', 'passage'),
        ('book', book.name if book != None else None),
        ('chapter', chapter.chapter_num if chapter != None else None),
        ('verses', verses),
    ))
    result.update(queries)
    return result

def browser():
    response.title = T("Browse")

    books_data = passage_db.executesql('''
select name, max(chapter_num) from chapter inner join book on chapter.book_id = book.id group by name order by book.id;
    ''')
    books_order = [x[0] for x in books_data]
    books = dict(x for x in books_data)
    result = dict(
        booksorder=json.dumps(books_order),
        books=json.dumps(books),
    )
    result.update(chapter_form())
    return result

def index():
    redirect(URL('browser', vars={}))
