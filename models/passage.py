from get_db_config import Configuration
import re


config = Configuration()

"""Passage dabatase"""
passage_db = DAL('mysql://%s:%s@%s/%s' % (config.passage_user,
                                          config.passage_passwd,
                                          config.passage_host,
                                          config.passage_db))


"""Book table"""
passage_db.define_table('book',
    Field('id', 'integer'),
    Field('name', 'string'),
    Field('first_m', 'integer'),
    Field('last_m', 'integer'),
    migrate=False)

"""Virtual field 'number of chapters' adds the chapter count to each book."""
passage_db.book.last_chapter_num = Field.Virtual(
    'last_chapter_num',
    lambda row: passage_db(passage_db.chapter.book_id == row.book.id).count())


"""Chapter table"""
passage_db.define_table('chapter',
    Field('id', 'integer'),
    Field('book_id', 'reference book'),
    Field('chapter_num', 'integer'),
    Field('first_m', 'integer'),
    Field('last_m', 'integer'),
    migrate=False)

passage_db.chapter.monads = Field.Method(
    lambda row: range(row.chapter.first_m, row.chapter.last_m + 1))


"""Verse table"""
passage_db.define_table('verse',
    Field('id', 'integer'),
    Field('chapter_id', 'reference chapter'),
    Field('verse_num', 'integer'),
    Field('text', 'string'),
    Field('xml', 'string'),
    Field('first_m', 'integer'),
    Field('last_m', 'integer'),
    migrate=False)


def xml_replace(xml):
    """Helper func. to transform the verse XML into HTML for the virtual field
    html.
    """
    return re.sub('<w m="(?P<monad>\d*)" t="(?P<trailer>[^"]*)">(?P<content>.*?)</w>',
                  '<span m="\g<monad>">\g<content></span>\g<trailer>',
                  xml)

"""Virtual field 'html' replaces the <w> tags in the xml field with <span> tags."""
passage_db.verse.html = Field.Virtual(
    'html',
    lambda row: xml_replace(row.verse.xml))

"""Virtual method 'monads' adds a list of all monads to each verse."""
passage_db.verse.monads = Field.Method(
    lambda row: range(row.verse.first_m, row.verse.last_m + 1))


"""Word verse table"""
passage_db.define_table('word_verse',
    Field('anchor', 'integer'),
    Field('verse_id', 'reference verse'),
    migrate=False)
