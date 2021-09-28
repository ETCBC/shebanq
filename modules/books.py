import json

from gluon import current

from blang import BOOK_LANGS, BOOK_TRANS, BOOK_NAMES


class BOOKS:
    def __init__(self):
        pass

    def getNames(self):
        jsinit = f"""
var bookLatin = {json.dumps(BOOK_NAMES["Hebrew"]["la"])};
var bookTrans = {json.dumps(BOOK_TRANS)};
var bookLangs = {json.dumps(BOOK_LANGS["Hebrew"])};
"""
        return dict(jsinit=jsinit)

    def get(self, vr):
        Caching = current.Caching

        return Caching.get(f"books_{vr}_", lambda: self.get_c(vr), None)

    def get_c(self, vr):
        # get book information: number of chapters per book
        PASSAGE_DBS = current.PASSAGE_DBS

        if vr in PASSAGE_DBS:
            booksData = PASSAGE_DBS[vr].executesql(
                """
select book.id, book.name, max(chapter_num)
from chapter inner join book
on chapter.book_id = book.id group by name order by book.id
;
"""
            )
            booksOrder = [x[1] for x in booksData]
            books = dict((x[1], x[2]) for x in booksData)
            bookIds = dict((x[1], x[0]) for x in booksData)
            bookName = dict((x[0], x[1]) for x in booksData)
            result = (books, booksOrder, bookIds, bookName)
        else:
            result = ({}, [], {}, {})
        return result
