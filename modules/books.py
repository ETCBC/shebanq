import json
from textwrap import dedent

from gluon import current

from constants import ALWAYS
from blang import BOOK_LANGS, BOOK_TRANS, BOOK_NAMES


class BOOKS:
    """All information about the names of bible books.

    The order of the books and the names of the books
    in all supported languages.

    This information is meant to be permanently cached.
    """
    def __init__(self):
        pass

    def getNames(self):
        """Send information about bible book names.

        The info consists of the latin book names,
        the languages in which we have translations for them,
        and a translation table for all book names.

        The info is wrapped in global Javascript variables,
        so that the whole client app can use the info.
        """
        jsinit = dedent(
            f"""
            var bookLatin = {json.dumps(BOOK_NAMES["Hebrew"]["la"])};
            var bookTrans = {json.dumps(BOOK_TRANS)};
            var bookLangs = {json.dumps(BOOK_LANGS["Hebrew"])};
            """
        )
        return dict(jsinit=jsinit)

    def get(self, vr):
        Caching = current.Caching

        return Caching.get(f"books_{vr}_", lambda: self.get_c(vr), ALWAYS)

    def get_c(self, vr):
        """get book information: number of chapters per book
        """
        PASSAGE_DBS = current.PASSAGE_DBS

        if vr in PASSAGE_DBS:
            booksData = PASSAGE_DBS[vr].executesql(
                dedent(
                    """
                    select book.id, book.name, max(chapter_num)
                    from chapter inner join book
                    on chapter.book_id = book.id group by name order by book.id
                    ;
                    """
                )
            )
            booksOrder = [x[1] for x in booksData]
            books = dict((x[1], x[2]) for x in booksData)
            bookIds = dict((x[1], x[0]) for x in booksData)
            bookName = dict((x[0], x[1]) for x in booksData)
            result = (books, booksOrder, bookIds, bookName)
        else:
            result = ({}, [], {}, {})
        return result
