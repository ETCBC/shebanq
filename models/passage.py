from get_db_config import Configuration


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
    migrate=False)


"""Verse table"""
passage_db.define_table('verse',
    Field('id', 'integer'),
    Field('chapter_id', 'reference chapter'),
    Field('verse_num', 'integer'),
    Field('text', 'string'),
    Field('xml', 'string'),
    migrate=False)

"""Virtual field 'html' replaces the <w> tags in the xml field with <span> tags."""
passage_db.verse.html = Field.Virtual(
    'html',
    lambda row: row.verse.xml.replace('</w>', '</span>').replace('<w', '<span'))

"""Virtual method 'monads' adds a list of all monads to each verse."""
passage_db.verse.monads = Field.Method(
    lambda row: [x['anchor'] for x in passage_db(
        passage_db.word_verse.verse_id == row.verse.id)
        .select(passage_db.word_verse.anchor)
        .as_list()]
)


"""Word verse table"""
passage_db.define_table('word_verse',
    Field('anchor', 'string'),
    Field('verse_id', 'reference verse'),
    migrate=False)
