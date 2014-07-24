import json
from itertools import groupby
from collections import defaultdict
import time


def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res
    return wrapper


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
        verses = passage_db(passage_db.verse.chapter_id == chapter).select()
    else:
        verses = []

    return verses


def get_verse(no_controller=True):
    chapter = get_chapter()
    verse_num = request.vars.verse
    if chapter and verse_num:
        verse = passage_db.verse(chapter_id=chapter.id, verse_num=verse_num)
    else:
        verse = None
    return verse


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


def highlighter_form(no_controller=True):
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


def process_highlighter_form(no_controller=True):
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


def verse_word_highlighter_form(no_controller=True):
    """ CONTROLLER HELPER
    Generate the verse-word highlighter form: highlight specified (nth) words
    in a specified verse.
    Verse field takes one integer.
    Words field takes comma or spaces seperated integers.
    """
    MY_PLACEHOLDER_STRING_WIDGET_WORDS = lambda field, value: SQLFORM.widgets.string.widget(field,
                                                                                            value,
                                                                                            _placeholder=T('Word nos. (comma separated)...'))
    MY_PLACEHOLDER_STRING_WIDGET_VERSE = lambda field, value: SQLFORM.widgets.string.widget(field,
                                                                                            value,
                                                                                            _placeholder=T('Verse number...'))
    form = SQLFORM.factory(Field('Verse', 'integer',
                                 required=IS_NOT_EMPTY(),
                                 default=request.vars.verse if request.vars.verse else None,
                                 widget=MY_PLACEHOLDER_STRING_WIDGET_VERSE),
                           Field('Words',
                                 default=request.vars.words if request.vars.words else None,
                                 widget=MY_PLACEHOLDER_STRING_WIDGET_WORDS),
                           table_name='verse_word_highlight_form',
                           submit_button=T('Highlight words'),
                           formstyle='ul',
                           _id='verse_word_highlighter_form',
                           )

    if form.process().accepted:
        verse = form.vars['Verse']
        words = [x.strip() for x in form.vars['Words'].split(',')]
        redirect(URL('browser', vars={'book': request.vars.book,
                                      'chapter': request.vars.chapter,
                                      'verse': verse,
                                      'words': ','.join(words)}))
    return form


def process_verse_word_highlighter_form(no_controller=True):
    """ CONTROLLER HELPER
    Process the verse-word highlighter form input and generate a JSON string
    list of monads to be processed (highlighted) by JQuery in the view.
    """
    verse = get_verse()
    words = request.vars.words
    if verse and words:
        # Transform the (nth) words of the verse into monads.
        words = [int(x.strip()) for x in request.vars.words.split(',')]  # Process the raw request variable words
        verse_monads = verse.monads()  # Get a list of in order monads in the verse
        monads = json.dumps([verse_monads[w - 1]
                             for w in words
                             if w < len(verse_monads) + 1])  # Map the words onto the monads
        # Notify the user of non-existing words
        not_in_verse = ', '.join(map(lambda x: str(x),
                                     filter(lambda x: x > len(verse_monads),
                                            words)))  # Out: '80, 90, 93' or ''
        if not_in_verse:
            response.flash = "Warning: word%s %s not in verse %i." % ('s' if len(not_in_verse.split(', ')) > 1 else '',
                                                                      not_in_verse,
                                                                      verse.verse_num)
    elif verse:
        # No words were specified so highlight all words/monads in the verse.
        monads = json.dumps(verse.monads())
    else:
        # No verse specified / empty form
        return dict()

    return dict(monads=monads, )


def get_queries_form(no_controller=True):
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


def intersect(a, b):
    return list(set(a) & set(b))


@print_timing
def group(input, chapter):
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

    [
        {'query': 10L, 'monad': 197563L},
        {'query': 7L, 'monad': 198280L},
        {'query': 9L, 'monad': 198228L},
        {'query': 10L, 'monad': 198142L},
        {'query': 5L, 'monad': 198090L}
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
    sorted_input = sorted(input, key=lambda x: x.query_id)
    groups = groupby(sorted_input, key=lambda x: x.query_id)
    r = []
    for k, v in groups:
        query = db.queries(k)
        monads = [(m.first_m, m.last_m) for m in v]
        json_monads = json.dumps(sorted(list(set(sum([intersect(xrange(x[0], x[1] + 1),
                                                                xrange(chapter.first_m, chapter.last_m + 1))
                                                      for x in monads],
                                                     [])))))  # You only want the monads that actually appear in the text to avoid massive overhead
        r.append({'query': query,
                  'monadsets': monads,
                  'json_monads': json_monads})
    return r


@print_timing
def alt_group(input, chapter):
    flattened_input = [{'query': x.query_id,
                        'monads': (x.first_m, x.last_m)}
                       for x in input]
    sorted_input = sorted(flattened_input, key=lambda x: x['query'])
    groups = groupby(sorted_input, key=lambda x: x['query'])
    r = []
    for k, v in groups:
        query = db.queries(k)
        monads = ([m['monads'] for m in v])
        json_monads = json.dumps(sorted(list(set(sum([intersect(xrange(x[0], x[1] + 1),
                                                                xrange(chapter.first_m, chapter.last_m + 1))
                                                      for x in monads],
                                                     [])))))  # You only want the monads that actually appear in the text to avoid massive overhead
        r.append({'query': query,
                  'monadsets': monads,
                  'json_monads': json_monads})
    return r


@print_timing
def alt_alt_group(input, chapter):
    res = defaultdict(list)
    for x in input:
        res[x.query_id].extend(intersect(xrange(x.first_m,
                                                x.last_m + 1),
                                         xrange(chapter.first_m,
                                                chapter.last_m + 1)))
    return res


def get_json_monads_from_group(group):
    """ HELPER
    Return a list of all the monads from a 'group'-ed query_monad query.
    """
    return json.dumps(sum([m['monads'] for m in group], []))


def monadset_in_text(m, t):
    """HELPER
    True if the monadset is in the text otherwise False.
    IN: (start monad, end monad), (start monad text, end monad text)
    OUT: True or False
    """
    return ((m[0] <= t[0] and m[1] >= t[0]) or
            (m[0] >= t[0] and m[0] <= t[1]))


@print_timing
def get_monadsets(chapter):
    does_monadset_overlap_with_chapter = monadset_in_text((db.monadsets.first_m,
                                                           db.monadsets.last_m),
                                                          (chapter.first_m,
                                                           chapter.last_m)).case(True, False)
    monadsets = map(lambda x: x.monadsets,
                    db().select(db.monadsets.query_id,
                                db.monadsets.first_m,
                                db.monadsets.last_m,
                                does_monadset_overlap_with_chapter))
    return monadsets


def process_get_queries_form(no_controller=True):
    """ CONTROLLER HELPER to process the get queries form.
    Return query_monads: a list of dictionaries of queries for a specific book
    and chapter and their associated monads.

    get queries =>
        get all monads in current chapter =>
            get corresponding queries
    """
    get_queries = request.vars.get_queries
    if bool(get_queries):
        chapter = get_chapter()
        monadsets = get_monadsets(chapter)
        query_monads = group(monadsets, chapter)
        #query_monads = alt_group(monadsets, chapter)
        #query_monads = alt_alt_group(monadsets, chapter)
    else:
        query_monads = []
    return dict(query_monads=query_monads,)


def browser():
    """ CONTROLLER
    Display the selected book-chapter and highlight monads.
    """
    forms = {'browse_form': browser_form(),
             'highlight_form': highlighter_form(),
             'get_queries_form': get_queries_form(),
             'verse_word_highlighter_form': verse_word_highlighter_form(), }

    browse = process_browser_form()
    highlight = process_highlighter_form()
    queries = process_get_queries_form()
    words = process_verse_word_highlighter_form()

    response.title = T("Browse")
    if 'verses' in browse and browse['verses']:
        response.subtitle = "%s - Chapter %s" % (browse['book'].name,
                                                 browse['chapter'].chapter_num)

    return dict(forms.items()
                + browse.items()
                + highlight.items()
                + queries.items()
                + words.items())


def index():
    redirect(URL('browser', vars={}))
