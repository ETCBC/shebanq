import json

from verse import Verse


class CHUNK:
    def __init__(self, Caching, passage_dbs, versions):
        self.Caching = Caching
        self.passage_dbs = passage_dbs
        self.versions = versions

    def get_books(self, vr):
        Caching = self.Caching

        return Caching.get(f"books_{vr}_", lambda: self.get_books_c(vr), None)

    def get_books_c(self, vr):
        # get book information: number of chapters per book
        passage_dbs = self.passage_dbs

        if vr in passage_dbs:
            books_data = passage_dbs[vr].executesql(
                """
select book.id, book.name, max(chapter_num)
from chapter inner join book
on chapter.book_id = book.id group by name order by book.id
;
"""
            )
            books_order = [x[1] for x in books_data]
            books = dict((x[1], x[2]) for x in books_data)
            book_id = dict((x[1], x[0]) for x in books_data)
            book_name = dict((x[0], x[1]) for x in books_data)
            result = (books, books_order, book_id, book_name)
        else:
            result = ({}, [], {}, {})
        return result

    def get_verse_simple(self, vr, bk, ch, vs):
        Caching = self.Caching

        return Caching.get(
            f"versej_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.get_verse_simple_c(vr, bk, ch, vs),
            None,
        )

    def get_verse_simple_c(self, vr, bk, ch, vs):
        passage_dbs = self.passage_dbs

        passage_db = passage_dbs[vr] if vr in passage_dbs else None
        msgs = []
        good = True
        data = dict()
        if passage_db is None:
            msgs.append(("Error", f"No such version: {vr}"))
            good = False
        if good:
            verse_info = passage_db.executesql(
                f"""
select verse.id, verse.text from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
where book.name = '{bk}' and chapter.chapter_num = {ch} and verse_num = {vs}
;
"""
            )
            if len(verse_info) == 0:
                msgs.append(("Error", f"No such verse: {bk} {ch}:{vs}"))
                good = False
            else:
                data = verse_info[0]
                vid = data[0]
                word_info = passage_db.executesql(
                    f"""
select word.word_phono, word.word_phono_sep
from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
where verse.id = {vid}
order by word_number
;
"""
                )
                data = dict(
                    text=data[1], phonetic="".join(x[0] + x[1] for x in word_info)
                )
        return json.dumps(dict(good=good, msgs=msgs, data=data), ensure_ascii=False)

    def get_verse(self, vr, bk, ch, vs, tr, msgs):
        Caching = self.Caching

        return Caching.get(
            f"verse_{vr}_{bk}_{ch}_{vs}_{tr}_",
            lambda: self.get_verse_c(vr, bk, ch, vs, tr, msgs),
            None,
        )

    def get_verse_c(self, vr, bk, ch, vs, tr, msgs):
        passage_dbs = self.passage_dbs

        material = Verse(
            passage_dbs,
            vr,
            bk,
            ch,
            vs,
            xml=None,
            word_data=None,
            tp="txt_il",
            tr=tr,
            mr=None,
        )
        good = True
        if len(material.word_data) == 0:
            msgs.append(("error", f"{bk} {ch}:{vs} does not exist"))
            good = False
        result = dict(
            good=good,
            msgs=msgs,
            material=material,
        )
        return result

    def get_clause_atom_fmonad(self, vr):
        Caching = self.Caching

        return Caching.get(
            f"clause_atom_f_{vr}_",
            lambda: self.get_clause_atom_fmonad_c(vr),
            None,
        )

    def get_clause_atom_fmonad_c(self, vr):
        passage_dbs = self.passage_dbs

        (books, books_order, book_id, book_name) = self.get_books(vr)
        sql = """
select book_id, ca_num, first_m
from clause_atom
;
"""
        ca_data = passage_dbs[vr].executesql(sql) if vr in passage_dbs else []
        clause_atom_first = {}
        for (bid, can, fm) in ca_data:
            bnm = book_name[bid]
            clause_atom_first.setdefault(bnm, {})[can] = fm
        return clause_atom_first

    def get_clause_atoms(self, vr, bk, ch, vs):
        Caching = self.Caching
        return Caching.get(
            f"clause_atoms_{vr}_{bk}_{ch}_{vs}_",
            lambda: self.get_clause_atoms_c(vr, bk, ch, vs),
            None,
        )

    def get_clause_atoms_c(self, vr, bk, ch, vs):
        # get clauseatoms for each verse
        passage_dbs = self.passage_dbs

        clause_atoms = []
        ca_data = (
            passage_dbs[vr].executesql(
                f"""
select
   distinct word.clause_atom_number
from
    verse
inner join
    word_verse on verse.id = word_verse.verse_id
inner join
    word on word.word_number = word_verse.anchor
inner join
    chapter on chapter.id = verse.chapter_id
inner join
    book on book.id = chapter.book_id
where
    book.name = '{bk}' and chapter.chapter_num = {ch} and verse.verse_num = {vs}
order by
    word.clause_atom_number
;
"""
            )
            if vr in passage_dbs
            else []
        )

        for (can,) in ca_data:
            clause_atoms.append(can)
        return clause_atoms
