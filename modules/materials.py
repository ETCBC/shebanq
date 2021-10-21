import json
from textwrap import dedent

from gluon import current

from constants import ALWAYS, ONE_HOUR
from versescontent import VERSESCONTENT
from helpers import iDecode, pagelist


RESULT_PAGE_SIZE = 20


class MATERIAL:
    """Responsible for the data for the main area of the page.

    See

    *   [{Material}][material]
    *   [∈ book][elem-book],
    *   [∈ chapter][elem-chapter],
    *   [∈ page][elem-page],
    """
    def __init__(self, Record, Word, Query, Note):
        self.Record = Record
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def page(self):
        Check = current.Check
        Record = self.Record

        mr = Check.field("material", "", "mr")
        qw = Check.field("material", "", "qw")
        vr = Check.field("material", "", "version")
        bk = Check.field("material", "", "book")
        ch = Check.field("material", "", "chapter")
        tp = Check.field("material", "", "tp")
        tr = Check.field("material", "", "tr")
        lang = Check.field("material", "", "lang")
        iidRep = Check.field("material", "", "iid")
        page = Check.field("material", "", "page")

        (authorized, msg) = Record.authRead(mr, qw, iidRep)
        if not authorized:
            return dict(
                version=vr,
                mr=mr,
                qw=qw,
                msg=msg,
                hits=0,
                results=0,
                pages=0,
                page=0,
                pagelist=json.dumps([]),
                material=None,
                slots=json.dumps([]),
            )
        return self.get(vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang)

    def getPassage(self, vr, bk, ch):
        Caching = current.Caching

        return Caching.get(
            f"passage_{vr}_{bk}_{ch}",
            lambda: self.getPassage_c(vr, bk, ch),
            ALWAYS,
        )

    def getPassage_c(self, vr, bookname, chapternum):
        PASSAGE_DBS = current.PASSAGE_DBS

        if bookname is None or chapternum is None or vr not in PASSAGE_DBS:
            return ({}, {})
        bookrecords = PASSAGE_DBS[vr].executesql(
            dedent(
                f"""
                select * from book where name = '{bookname}'
                ;
                """
            ),
            as_dict=True,
        )
        book = bookrecords[0] if bookrecords else {}
        if book and "id" in book:
            chapterrecords = PASSAGE_DBS[vr].executesql(
                dedent(
                    f"""
                    select * from chapter
                    where chapter_num = {chapternum} and book_id = {book["id"]}
                    ;
                    """
                ),
                as_dict=True,
            )
            chapter = chapterrecords[0] if chapterrecords else {}
        else:
            chapter = {}
        return (book, chapter)

    def get(self, vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang):
        Caching = current.Caching

        mrrep = "m" if mr == "m" else qw
        book = bk if mr == "m" else iidRep
        chapter = ch if mr == "m" else page
        return Caching.get(
            f"verses_{vr}_{mrrep}_{book}_{chapter}_{tp}_{tr}_{lang}_",
            lambda: self.get_c(vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang),
            ONE_HOUR,
        )

    def get_c(self, vr, mr, qw, bk, iidRep, ch, page, tp, tr, lang):
        Word = self.Word
        Query = self.Query
        Note = self.Note

        if mr == "m":
            (book, chapter) = self.getPassage(vr, bk, ch)
            material = (
                VERSESCONTENT(vr, mr, chapter=chapter["id"], tp=tp, tr=tr, lang=lang)
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
                slots=json.dumps([]),
            )
        elif mr == "r":
            (iid, keywords) = (None, None)
            if iidRep is not None:
                (iid, keywords) = iDecode(qw, iidRep)
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
                    slots=json.dumps([]),
                )
            else:
                (nSlots, slotSets) = (
                    Query.read(vr, iid)
                    if qw == "q"
                    else Word.read(vr, iid)
                    if qw == "w"
                    else Note.read(vr, iid, keywords)
                )
                (nresults, npages, verses, slots) = self.getPagination(
                    vr, page, slotSets
                )
                material = VERSESCONTENT(vr, mr, verses, tp=tp, tr=tr, lang=lang)
                result = dict(
                    mr=mr,
                    qw=qw,
                    msg=None,
                    hits=nSlots,
                    results=nresults,
                    pages=npages,
                    page=page,
                    pagelist=json.dumps(pagelist(page, npages, 10)),
                    material=material,
                    slots=json.dumps(slots),
                )
        else:
            result = dict()
        return result

    def getPagination(self, vr, p, slotSets):
        Caching = current.Caching
        PASSAGE_DBS = current.PASSAGE_DBS

        verseBoundaries = (
            Caching.get(
                f"verse_boundaries_{vr}_",
                lambda: PASSAGE_DBS[vr].executesql(
                    dedent(
                        """
                        select first_m, last_m from verse order by id
                        ;
                        """
                    )
                ),
                ALWAYS,
            )
            if vr in PASSAGE_DBS
            else []
        )
        m = 0  # slot range index, walking through slotSets
        v = 0  # verse id, walking through verseBoundaries
        nvp = 0  # number of verses added to current page
        nvt = 0  # number of verses added in total
        nM = len(slotSets)
        nV = len(verseBoundaries)
        curPage = 1  # current page
        verseIds = []
        verseSlots = set()
        lastVerse = -1
        while m < nM and v < nV:
            if nvp == RESULT_PAGE_SIZE:
                nvp = 0
                curPage += 1
            (vB, vE) = verseBoundaries[v]
            (mB, mE) = slotSets[m]
            if vE < mB:
                v += 1
                continue
            if mE < vB:
                m += 1
                continue
            # now vE >= mB and mE >= vB so one of the following holds
            #           vvvvvv
            #       mmmmm
            #       mmmmmmmmmmmmmmm
            #            mmm
            #            mmmmmmmmmmmmm
            # so (vB, vE) and (mB, mE) overlap
            # so add v to the result pages and go to the next verse
            # and add p to the highlight list if on the selected page
            if v != lastVerse:
                if curPage == p:
                    verseIds.append(v)
                    lastVerse = v
                nvp += 1
                nvt += 1
            if lastVerse == v:
                clippedSLots = set(range(max(vB, mB), min(vE, mE) + 1))
                verseSlots |= clippedSLots
            if curPage != p:
                v += 1
            else:
                if mE < vE:
                    m += 1
                else:
                    v += 1

        if nvp == 0:
            # no verses on last current page, so it is empty, so discard it
            curPage -= 1
        verses = verseIds if p <= curPage and len(verseIds) else None
        return (nvt, curPage if nvt else 0, verses, list(verseSlots))
