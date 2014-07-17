import json
from random import randint
from itertools import groupby


def get_books():
    """ HELPER
    Return all the books as Web2Py Rows with an added 'number of chapters'
    field.
    """
    return passage_db(passage_db.book.id > 0).select(cache=(cache.ram, 3600),
                                                     cacheable=True)


def get_book():
    """ HELPER
    Return a specific book based on a request variable.
    """
    book_name = request.vars.book or request.vars.Book  # request.vars.Book for the Ajax queries
    if book_name:
        book = passage_db.book(name=book_name)
    else:
        book = None
    return book


def get_chapter():
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


def get_verses():
    """ HELPER
    Return all verses from a book-chapter specified in the request variable.
    """
    chapter = get_chapter()
    if chapter:
        verses = passage_db(passage_db.verse.chapter_id == chapter).select()
    else:
        verses = []

    return verses


def max_chapters():
    """ HELPER
    Return the maximum number of chapters in any book.
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


def browser_form():
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


def process_browser_form():
    """ CONTROLLER HELPER
    Process the browser form input and produce the book, chapter and verses.
    """
    book = get_book()
    chapter = get_chapter()
    verses = get_verses()

    return locals()


def highlighter_form():
    """ CONTROLLER HELPER
    Generate the highlight form.
    Monads to highlight field takes comma or spaces seperated integers.
    """
    MY_PLACEHOLDER_STRING_WIDGET = lambda field, value: SQLFORM.widgets.string.widget(field,
                                                                                      value,
                                                                                      _placeholder='Monads (comma separated)...')
    form = SQLFORM.factory(Field('Monads to highlight',
                                 requires=IS_NOT_EMPTY(),
                                 default=request.vars.monads if request.vars.monads else None,
                                 widget=MY_PLACEHOLDER_STRING_WIDGET),
                           table_name='highlight_form',
                           submit_button='Highlight monads',
                           formstyle='ul',
                           _id='highlighter_form',
                           )

    if form.process().accepted:
        monads = [x.strip() for x in form.vars['Monads to highlight'].split(',')]
        redirect(URL('browser', vars={'book': request.vars.book,
                                      'chapter': request.vars.chapter,
                                      'monads': ' '.join(monads)}))

    return form


def process_highlighter_form():
    """ CONTROLLER HELPER
    Process the highlighter form input and generate a JSON string list of
    monads to be processed by JQuery in the view.
    """
    monads = request.vars.monads
    if monads:
        monads = json.dumps([int(x.strip()) for x in monads.split(' ')])
    else:
        monads = []

    return dict(monads=monads, )


def get_queries_form():
    """ CONTROLLER HELPER
    Generate the get queries form.
    """
    form = SQLFORM.factory(submit_button='Get related queries',
                           table_name='get_queries_form',
                           formstyle='ul',
                           _id='get_queries_form')

    if form.process().accepted:
        redirect(URL('browser', vars={'book': request.vars.book,
                                      'chapter': request.vars.chapter,
                                      'get_queries': True}))

    return form


def group(input):
    """ HELPER for process_get_queries_form
    Reorganise a query_monad query.

    Input (query dict):
    [
        {'query': 10L, 'id': 996L, 'monad': 197563L},
        {'query': 7L, 'id': 602L, 'monad': 198280L},
        {'query': 9L, 'id': 803L, 'monad': 198228L},
        {'query': 10L, 'id': 911L, 'monad': 198142L},
        {'query': 5L, 'id': 423L, 'monad': 198090L}
    ]

    Grouped query dict:
    [
        {'query': 5L, 'monads': [198090L]},
        {'query': 7L, 'monads': [198280L]},
        {'query': 9L, 'monads': [198228L]},
        {'query': 10L, 'monads': [197563L, 198142L]}
    ]

    Output (replace the query id with the actual query row object):
    [
        {'query': <Row {'query': 'Dit is query 5.', 'id': 5L}>,
         'monads': [198090L]},
        {'query': <Row {'query': 'Dit is query 7.', 'id': 7L}>,
         'monads': [198280L]},
        {'query': <Row {'query': 'Dit is query 9.', 'id': 9L}>,
         'monads': [198228L]},
        {'query': <Row {'query': 'Dit is query 10.', 'id': 10L}>,
         'monads': [197563L, 198142L]}
    ]
    """
    sorted_input = sorted(input, key=lambda x: x['query'])
    groups = groupby(sorted_input, key=lambda x: x['query'])
    r = []
    for k, v in groups:
        query = query_db.query(id=k)
        monads = [x['monad'] for x in v]
        json_monads = json.dumps(monads)
        r.append({'query': query,
                  'monads': monads,
                  'json_monads': json_monads})
    return r


def get_json_monads_from_group(group):
    """ HELPER
    Return a list of all the monads from a 'group'-ed query_monad query.
    """
    return json.dumps(sum([m['monads'] for m in group], []))


def process_get_queries_form():
    """ CONTROLLER HELPER to process the get queries form.
    Return:
    * query_monads: a list of dictionaries of queries for a specific book
    and chapter and their associated monads;
    * monads: a flat list of the monad numbers in query_monads.

    get queries =>
        get all monads in current chapter =>
            get corresponding queries
    """
    get_queries = request.vars.get_queries
    if bool(get_queries):
        all_monads_in_all_chapter_verses = sum([v.monads() for v in get_verses()], [])  # Flatten list of lists of monads
        query_monads = group(query_db(query_db.query_monad.monad.belongs(all_monads_in_all_chapter_verses)).select().as_dict().values())
    else:
        query_monads = []
    return dict(query_monads=query_monads,)


def generate_monads():
    """ HELPER
    Generate monads.
    Usage: just temporarily add it to a controller to generate the monads.
    """
    query_db.query.truncate()
    query_db.query_monad.truncate()
    for x in xrange(1, 11):
        # Create the Query object
        query_db.query.insert(query="Dit is query %i." % x)
        query = query_db(query_db.query.id == x).select()[0]
        for y in xrange(0, 100):
            query_db.query_monad.insert(query=query, monad=randint(0, 430000))


def browser():
    """ CONTROLLER
    Display the selected book-chapter and highlight monads.
    """
    forms = {'browse_form': browser_form(),
             'highlight_form': highlighter_form(),
             'get_queries_form': get_queries_form()}

    browse = process_browser_form()
    highlight = process_highlighter_form()
    queries = process_get_queries_form()

    response.title = T("Browse")
    if 'verses' in browse and browse['verses']:
        response.subtitle = "%s - Chapter %s" % (browse['book'].name,
                                                 browse['chapter'].chapter_num)

    return dict(forms.items()
                + browse.items()
                + highlight.items()
                + queries.items())
