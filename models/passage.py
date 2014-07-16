import logging
import os
from ConfigParser import SafeConfigParser


class Configuration():

    def __init__(self):
        parser = SafeConfigParser()
        logging.debug("Trying to find the configuration file for shebanq_db.passage")
        c_path = ['/usr/local/shebanq/shebanq_db.cfg', 'shebanq_db.cfg']
        logging.debug("Trying these locations: " + str(c_path))
        for path in c_path:
            if os.path.isfile(path):
                break
        if not os.path.isfile(path):
            logging.error("No configuration file found in locations " + str(c_path))
            raise Exception("No configuration file found in locations " + str(c_path))

        logging.info("Trying to configure shebanq_db.passage with configuration found at " + path)
        try:
            parser.read(path)
            self.passage_host = parser.get('passage', 'host')
            self.passage_user = parser.get('passage', 'user')
            self.passage_passwd = parser.get('passage', 'passwd')
            self.passage_db = parser.get('passage', 'db')
        except:
            logging.error("A correct configuration file is expected at " + path)

config = Configuration()

passage_db = DAL('mysql://%s:%s@%s/%s' % (config.passage_user,
                                          config.passage_passwd,
                                          config.passage_host,
                                          config.passage_db))

passage_db.define_table('book',
    Field('id', 'integer'),
    Field('name', 'string'),
    migrate=False)

# Add the 'number of chapters' to the rows in the book table as a virtual field.
passage_db.book.last_chapter_num = Field.Virtual(
    'last_chapter_num',
    lambda row: passage_db(passage_db.chapter.book_id == row.book.id).count())

passage_db.define_table('chapter',
    Field('id', 'integer'),
    Field('book_id', 'reference book'),
    Field('chapter_num', 'integer'),
    migrate=False)

passage_db.define_table('verse',
    Field('id', 'integer'),
    Field('chapter_id', 'reference chapter'),
    Field('verse_num', 'integer'),
    Field('text', 'string'),
    Field('xml', 'string'),
    migrate=False)

"""html field that replaces the <w> tags in the xml field with <span> tags."""
passage_db.verse.html = Field.Virtual(
    'html',
    lambda row: row.verse.xml.replace('</w>', '</span>').replace('<w', '<span'))

passage_db.verse.monads = Field.Method(
    lambda row: [x['anchor'] for x in passage_db(
        passage_db.word_verse.verse_id == row.verse.id)
        .select(passage_db.word_verse.anchor)
        .as_list()]
)

passage_db.define_table('word_verse',
    Field('anchor', 'string'),
    Field('verse_id', 'reference verse'),
    migrate=False)
