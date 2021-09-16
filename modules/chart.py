import json

from helpers import flatten, iid_decode

BLOCK_SIZE = 500


class CHART:
    def __init__(self, Chunk, Word, Query, Note):
        self.Chunk = Chunk
        self.Word = Word
        self.Query = Query
        self.Note = Note

    def get(self, vr, qw, iidrep):
        Caching = self.Caching

        return Caching.get(
            f"chart_{vr}_{qw}_{iidrep}_",
            lambda: self.get_c(vr, qw, iidrep),
            None,
        )

    def get_c(self, vr, qw, iidrep):
        Query = self.Query
        Word = self.Word
        Note = self.Note

        (iid, kw) = iid_decode(qw, iidrep)
        (nmonads, monad_sets) = (
            Query.load(vr, iid)
            if qw == "q"
            else Word.load(vr, iid)
            if qw == "w"
            else Note.load(vr, iid, kw)
        )
        result = self.compose(vr, monad_sets)
        result.update(qw=qw)
        return result

    def get_blocks(self, vr):
        Caching = self.Caching
        return Caching.get(f"blocks_{vr}_", lambda: self.get_blocks_c(vr), None)

    def get_blocks_c(self, vr):
        """get block info
        For each monad: to which block it belongs,
        for each block: book and chapter number of first word.
        Possibly there are gaps between books.
        """
        passage_dbs = self.passage_dbs

        if vr not in passage_dbs:
            return ([], {})
        book_monads = passage_dbs[vr].executesql(
            """
select name, first_m, last_m from book
;
"""
        )
        chapter_monads = passage_dbs[vr].executesql(
            """
select chapter_num, first_m, last_m from chapter
;
    """
        )
        m = -1
        cur_blk_f = None
        cur_blk_size = 0
        cur_bk_index = 0
        cur_ch_index = 0
        (cur_bk, cur_bk_f, cur_bk_l) = book_monads[cur_bk_index]
        (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
        blocks = []
        block_mapping = {}

        def get_curpos_info(n):
            (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
            chapter_len = cur_ch_l - cur_ch_f + 1
            fraction = float(n - cur_ch_f) / chapter_len
            rep = (
                f"{cur_ch}.Z"
                if n == cur_ch_l
                else f"{cur_ch}.z"
                if round(10 * fraction) == 10
                else "{cur_ch + fraction:0.1f}"
            )
            return (cur_ch, rep)

        while True:
            m += 1
            if m > cur_bk_l:
                size = round((float(cur_blk_size) / BLOCK_SIZE) * 100)
                blocks.append((cur_bk, cur_blk_f, get_curpos_info(m - 1), size))
                cur_blk_size = 0
                cur_bk_index += 1
                if cur_bk_index >= len(book_monads):
                    break
                else:
                    (cur_bk, cur_bk_f, cur_bk_l) = book_monads[cur_bk_index]
                    cur_ch_index += 1
                    (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
                    cur_blk_f = get_curpos_info(m)
            if cur_blk_size == BLOCK_SIZE:
                blocks.append((cur_bk, cur_blk_f, get_curpos_info(m - 1), 100))
                cur_blk_size = 0
            if m > cur_ch_l:
                cur_ch_index += 1
                if cur_ch_index >= len(chapter_monads):
                    break
                else:
                    (cur_ch, cur_ch_f, cur_ch_l) = chapter_monads[cur_ch_index]
            if m < cur_bk_f:
                continue
            if m < cur_ch_f:
                continue
            if cur_blk_size == 0:
                cur_blk_f = get_curpos_info(m)
            block_mapping[m] = len(blocks)
            cur_blk_size += 1
        return (blocks, block_mapping)

    def compose(self, vr, monad_sets):
        # get data for a chart of the monadset: organized by book and block
        # return a dict keyed by book, with values lists of blocks
        # (chapter num, start point, end point, number of results, size)

        Chunk = self.Chunk

        monads = flatten(monad_sets)
        chart = {}
        chart_order = []
        if len(monads):
            (books, books_order, book_id, book_name) = Chunk.get_books(vr)
            (blocks, block_mapping) = self.get_blocks(vr)
            results = {}

            for bl in range(len(blocks)):
                results[bl] = 0
            for bk in books_order:
                chart[bk] = []
                chart_order.append(bk)
            for m in monads:
                results[block_mapping[m]] += 1
            for bl in range(len(blocks)):
                (bk, ch_start, ch_end, size) = blocks[bl]
                r = results[bl]
                chart[bk].append((ch_start[0], ch_start[1], ch_end[1], r, size))

        return dict(chart=json.dumps(chart), chart_order=json.dumps(chart_order))
