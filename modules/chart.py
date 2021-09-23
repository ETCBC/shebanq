import json

from helpers import flatten, iDecode

BLOCK_SIZE = 500


class CHART:
    def __init__(self, Pieces, Word, Query, Note):
        self.Pieces = Pieces
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def get(self, vr, qw, iidRep, msg):
        Caching = self.Caching

        return Caching.get(
            f"chart_{vr}_{qw}_{iidRep}_",
            lambda: self.get_c(vr, qw, iidRep),
            None,
        )

    def get_c(self, vr, qw, iidRep):
        Query = self.Query
        Word = self.Word
        Note = self.Note

        (iid, keywords) = iDecode(qw, iidRep)
        (nSlots, slotSets) = (
            Query.read(vr, iid)
            if qw == "q"
            else Word.read(vr, iid)
            if qw == "w"
            else Note.read(vr, iid, keywords)
        )
        result = self.compose(vr, slotSets)
        result.update(qw=qw)
        return result

    def getBlocks(self, vr):
        Caching = self.Caching
        return Caching.get(f"blocks_{vr}_", lambda: self.getBlocks_c(vr), None)

    def getBlocks_c(self, vr):
        """get block info
        For each slot: to which block it belongs,
        for each block: book and chapter number of first word.
        Possibly there are gaps between books.
        """
        PASSAGE_DBS = self.PASSAGE_DBS

        if vr not in PASSAGE_DBS:
            return ([], {})
        bookSlots = PASSAGE_DBS[vr].executesql(
            """
select name, first_m, last_m from book
;
"""
        )
        chapterSlots = PASSAGE_DBS[vr].executesql(
            """
select chapter_num, first_m, last_m from chapter
;
    """
        )
        m = -1
        curBlkF = None
        curBlkSize = 0
        curBkIndex = 0
        curChpIndex = 0
        (curBk, curBkFirst_m, curBkLast_m) = bookSlots[curBkIndex]
        (curChp, curChpFirst_m, curChpLast_m) = chapterSlots[curChpIndex]
        blocks = []
        blockMapping = {}

        def getCurposInfo(n):
            (curChp, curChpFirst_m, curChpLast_m) = chapterSlots[curChpIndex]
            chapterLen = curChpLast_m - curChpFirst_m + 1
            fraction = float(n - curChpFirst_m) / chapterLen
            rep = (
                f"{curChp}.Z"
                if n == curChpLast_m
                else f"{curChp}.z"
                if round(10 * fraction) == 10
                else "{curChp + fraction:0.1f}"
            )
            return (curChp, rep)

        while True:
            m += 1
            if m > curBkLast_m:
                size = round((float(curBlkSize) / BLOCK_SIZE) * 100)
                blocks.append((curBk, curBlkF, getCurposInfo(m - 1), size))
                curBlkSize = 0
                curBkIndex += 1
                if curBkIndex >= len(bookSlots):
                    break
                else:
                    (curBk, curBkFirst_m, curBkLast_m) = bookSlots[curBkIndex]
                    curChpIndex += 1
                    (curChp, curChpFirst_m, curChpLast_m) = chapterSlots[curChpIndex]
                    curBlkF = getCurposInfo(m)
            if curBlkSize == BLOCK_SIZE:
                blocks.append((curBk, curBlkF, getCurposInfo(m - 1), 100))
                curBlkSize = 0
            if m > curChpLast_m:
                curChpIndex += 1
                if curChpIndex >= len(chapterSlots):
                    break
                else:
                    (curChp, curChpFirst_m, curChpLast_m) = chapterSlots[curChpIndex]
            if m < curBkFirst_m:
                continue
            if m < curChpFirst_m:
                continue
            if curBlkSize == 0:
                curBlkF = getCurposInfo(m)
            blockMapping[m] = len(blocks)
            curBlkSize += 1
        return (blocks, blockMapping)

    def compose(self, vr, slotSets):
        # get data for a chart of the slotset: organized by book and block
        # return a dict keyed by book, with values lists of blocks
        # (chapter num, start point, end point, number of results, size)

        Pieces = self.Pieces

        slots = flatten(slotSets)
        chart = {}
        chartOrder = []
        if len(slots):
            (books, booksOrder, bookIds, bookName) = Pieces.getBooks(vr)
            (blocks, blockMapping) = self.getBlocks(vr)
            results = {}

            for bl in range(len(blocks)):
                results[bl] = 0
            for bk in booksOrder:
                chart[bk] = []
                chartOrder.append(bk)
            for m in slots:
                results[blockMapping[m]] += 1
            for bl in range(len(blocks)):
                (bk, chpStart, chpEnd, size) = blocks[bl]
                r = results[bl]
                chart[bk].append((chpStart[0], chpStart[1], chpEnd[1], r, size))

        return dict(chart=json.dumps(chart), chartOrder=json.dumps(chartOrder))
