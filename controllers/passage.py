from gluon.custom_import import track_changes; track_changes(True)

import json
from itertools import groupby

from render import Verses, Viewsettings

def get_books(no_controller=True):
    """ HELPER
    Return all the books as Web2Py Rows with an added 'number of chapters'
    field.
    """
    return passage_db().select(passage_db.book.ALL,
                               cache=(cache.ram, 3600),
                               cacheable=True)


def get_book(no_controller=True):
    """ HELPER
    Return a specific book based on a request variable.
    """
    book_name = request.vars.book or request.vars.Book  # request.vars.Book for the Ajax queries
    if book_name:
        book = passage_db.book(name=book_name)
    else:
        book = None
    return book


def get_chapter(no_controller=True):
    """ HELPER
    Return a specific chapter based on a book and chapter in the request
    variable.
    """
    book = get_book()
    chapter_num = request.vars.chapter
    if book and chapter_num:
        chapter = passage_db.chapter(chapter_num=chapter_num, book_id=book)
    else:
        chapter = None
    return chapter


def get_verses(no_controller=True):
    """ HELPER
    Return all verses from a book-chapter specified in the request variable.
    """
    chapter = get_chapter()
    if chapter:
        verses = Verses(passage_db, 'passage', chapter=chapter.id)
    else:
        verses = None
    return verses


def max_chapters(no_controller=True):
    """ HELPER
    Find the largest number of chapters in all books.

    E.g.:
    book1 has 10 chapters,
    book2 has 25 chapters,
    book3 has 15 chapters.
    Returns: 25.
    """
    max = passage_db.chapter.chapter_num.max()
    return passage_db().select(max,
                               cache=(cache.ram, 3600),
                               cacheable=True).first()[max]


def last_chapter_num():
    """ HELPER
    Return the last chapter number of a book from a request variable.
    Used in an Ajax query.
    """
    return get_book().last_chapter_num


def browser_form(no_controller=True):
    """ CONTROLLER HELPER
    Generate and process the book and chapter option form.
    """
    form = SQLFORM.factory(Field('Book',
                                 'select',
                                 requires=IS_IN_SET([b.name for b in get_books()]),
                                 default=request.vars.book if request.vars.book else None),
                           Field('Chapter',
                                 'select',
                                 requires=IS_IN_SET(range(1, max_chapters() + 1)),
                                 default=request.vars.chapter if request.vars.chapter else None),
                           table_name='verses_form',
                           submit_button='View',
                           _id='verses_form',
                           formstyle='ul',)

    if form.process().accepted:
        redirect(URL('browser', vars={'book': form.vars.Book,
                                      'chapter': form.vars.Chapter}))

    return form


def process_browser_form(no_controller=True):
    """ CONTROLLER HELPER
    Process the browser form input and produce the book, chapter and verses.
    """
    book = get_book()
    chapter = get_chapter()
    verses = get_verses()

    return locals()


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
        r.append({'query': query,
                  'monadsets': monads,
                  'json_monads': json_monads})
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
           from monadsets inner join queries on monadsets.query_id = queries.id and queries.is_published = 'T'
           WHERE (first_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
                 (last_m BETWEEN {chapter_first_m} AND {chapter_last_m}) OR
                 ({chapter_first_m} BETWEEN first_m AND last_m);""".format(chapter_last_m=chapter.last_m,
                                                                           chapter_first_m=chapter.first_m),
                         as_dict=True)


def query_form(): return query_form_generic()

def query_form_generic(viewsettings=None):
    chapter = get_chapter()
    monadsets = get_monadsets_MySQL(chapter)
    query_monads = group_MySQL(monadsets)
    if viewsettings == None: viewsettings = Viewsettings('passage')
    return dict(
        query_monads=query_monads,
        viewsettings=viewsettings
    )

def browser():
    """ CONTROLLER
    Display the selected book-chapter and highlight monads.
    """
    forms = {'browse_form': browser_form()}

    browse = process_browser_form()
    viewsettings = Viewsettings('passage')
    queries = query_form_generic(viewsettings=viewsettings) if viewsettings.query_view['qget'] and browse['chapter'] else dict(query_monads=[], viewsettings=viewsettings)

    response.title = T("Browse")
    if 'verses' in browse and browse['verses']:
        response.subtitle = "%s - Chapter %s" % (browse['book'].name,
                                                 browse['chapter'].chapter_num)

    word_monads = []
    if page_kind == 'passage':
        word_monads = [('aap, noot')]

    return dict(forms.items()
                + browse.items()
                + queries.items()
                + [('word_monads', word_monads)]
                + [('page_kind', 'passage')]
    )

def index():
    redirect(URL('browser', vars={}))
