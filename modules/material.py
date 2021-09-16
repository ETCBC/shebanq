import json

from verses import Verses
from helpers import iid_decode, pagelist


RESULT_PAGE_SIZE = 20


class MATERIAL:
    def __init__(self, Caching, passage_dbs):
        self.Caching = Caching
        self.passage_dbs = passage_dbs

    def get_passage(self, vr, bk, ch):
        Caching = self.Caching

        return Caching.get(
            "passage_{vr}_{bk}_{ch}",
            lambda: self.get_passage_c(vr, bk, ch),
            None,
        )

    def get_passage_c(self, vr, bookname, chapternum):
        passage_dbs = self.passage_dbs

        if bookname is None or chapternum is None or vr not in passage_dbs:
            return ({}, {})
        bookrecords = passage_dbs[vr].executesql(
            f"""
select * from book where name = '{bookname}'
;
""",
            as_dict=True,
        )
        book = bookrecords[0] if bookrecords else {}
        if book and "id" in book:
            chapterrecords = passage_dbs[vr].executesql(
                f"""
select * from chapter where chapter_num = {chapternum} and book_id = {book["id"]}
;
""",
                as_dict=True,
            )
            chapter = chapterrecords[0] if chapterrecords else {}
        else:
            chapter = {}
        return (book, chapter)

    def get(self, vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang):
        Caching = self.Caching

        mrrep = "m" if mr == "m" else qw
        book = bk if mr == "m" else iidrep
        chapter = (ch if mr == "m" else page,)
        return Caching.get(
            f"verses_{vr}_{mrrep}_{book}_{chapter}_{tp}_{tr}_{lang}_",
            lambda: self.get_c(vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang),
            None,
        )

    def get_c(self, vr, mr, qw, bk, iidrep, ch, page, tp, tr, lang):
        Word = self.Word
        Query = self.Query
        Note = self.Note
        passage_dbs = self.passage_dbs

        if mr == "m":
            (book, chapter) = self.get_passage(vr, bk, ch)
            material = (
                Verses(
                    passage_dbs, vr, mr, chapter=chapter["id"], tp=tp, tr=tr, lang=lang
                )
                if chapter
                else None
            )
            result = dict(
                mr=mr,
                qw=qw,
                hits=0,
                msg=f"{bk} {ch} does not exist" if not chapter else None,
                results=len(material.verses) if material else 0,
                pages=1,
                material=material,
                monads=json.dumps([]),
            )
        elif mr == "r":
            (iid, kw) = (None, None)
            if iidrep is not None:
                (iid, kw) = iid_decode(qw, iidrep)
            if iid is None:
                kind = "query" if qw == "q" else "word" if qw == "w" else "note set"
                msg = f"No {kind} selected"
                result = dict(
                    mr=mr,
                    qw=qw,
                    msg=msg,
                    hits=0,
                    results=0,
                    pages=0,
                    page=0,
                    pagelist=json.dumps([]),
                    material=None,
                    monads=json.dumps([]),
                )
            else:
                (nmonads, monad_sets) = (
                    Query.load(vr, iid)
                    if qw == "q"
                    else Word.load(vr, iid)
                    if qw == "w"
                    else Note.load(vr, iid, kw)
                )
                (nresults, npages, verses, monads) = self.get_pagination(
                    vr, page, monad_sets
                )
                material = Verses(passage_dbs, vr, mr, verses, tp=tp, tr=tr, lang=lang)
                result = dict(
                    mr=mr,
                    qw=qw,
                    msg=None,
                    hits=nmonads,
                    results=nresults,
                    pages=npages,
                    page=page,
                    pagelist=json.dumps(pagelist(page, npages, 10)),
                    material=material,
                    monads=json.dumps(monads),
                )
        else:
            result = dict()
        return result

    def get_pagination(self, vr, p, monad_sets):
        Caching = self.Caching
        passage_dbs = self.passage_dbs

        verse_boundaries = (
            Caching.get(
                f"verse_boundaries_{vr}_",
                lambda: passage_dbs[vr].executesql(
                    """
select first_m, last_m from verse order by id
;
"""
                ),
                None,
            )
            if vr in passage_dbs
            else []
        )
        m = 0  # monad range index, walking through monad_sets
        v = 0  # verse id, walking through verse_boundaries
        nvp = 0  # number of verses added to current page
        nvt = 0  # number of verses added in total
        lm = len(monad_sets)
        lv = len(verse_boundaries)
        cur_page = 1  # current page
        verse_ids = []
        verse_monads = set()
        last_v = -1
        while m < lm and v < lv:
            if nvp == RESULT_PAGE_SIZE:
                nvp = 0
                cur_page += 1
            (v_b, v_e) = verse_boundaries[v]
            (m_b, m_e) = monad_sets[m]
            if v_e < m_b:
                v += 1
                continue
            if m_e < v_b:
                m += 1
                continue
            # now v_e >= m_b and m_e >= v_b so one of the following holds
            #           vvvvvv
            #       mmmmm
            #       mmmmmmmmmmmmmmm
            #            mmm
            #            mmmmmmmmmmmmm
            # so (v_b, v_e) and (m_b, m_e) overlap
            # so add v to the result pages and go to the next verse
            # and add p to the highlight list if on the selected page
            if v != last_v:
                if cur_page == p:
                    verse_ids.append(v)
                    last_v = v
                nvp += 1
                nvt += 1
            if last_v == v:
                clipped_m = set(range(max(v_b, m_b), min(v_e, m_e) + 1))
                verse_monads |= clipped_m
            if cur_page != p:
                v += 1
            else:
                if m_e < v_e:
                    m += 1
                else:
                    v += 1

        verses = verse_ids if p <= cur_page and len(verse_ids) else None
        return (nvt, cur_page if nvt else 0, verses, list(verse_monads))
