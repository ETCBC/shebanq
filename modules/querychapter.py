import time

from helpers import debug


class QUERYCHAPTER:
    def __init__(self, Caching, db, passage_dbs):
        self.Caching = Caching

    def makeQCindex(self, vr):
        Caching = self.Caching

        Caching.get(f"qcindex_{vr}_", lambda: self.makeQCindex_c(vr), None)

    def makeQCindex_c(self, vr):
        Caching = self.Caching
        db = self.db
        passage_dbs = self.passage_dbs

        debug(f"o-o-o making chapter-query index for version {vr} ...")
        startTime = time.time()

        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        mFromCh = Caching.get(
            f"mFromCh_{vr}_",
            lambda: {},
            None,
        )
        chFromM = Caching.get(
            f"chFromM_{vr}_",
            lambda: {},
            None,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            None,
        )
        chaptersFromQuery = Caching.get(
            f"chaptersFromQuery_{vr}_",
            lambda: {},
            None,
        )

        chapterSQL = """
select id, first_m, last_m from chapter
;
"""
        chapterList = passage_dbs[vr].executesql(chapterSQL)
        for (cid, first_m, last_m) in chapterList:
            for m in range(first_m, last_m + 1):
                chFromM[m] = cid
                mFromCh[cid] = (first_m, last_m)
        resultSQL = f"""
select
    query_exe.query_id as query_id, first_m, last_m, query_exe.is_published as qpub
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and
    query_exe.executed_on >= query_exe.modified_on
inner join query on
    query.id = query_exe.query_id and query.is_shared = 'T'
;
"""
        results = db.executesql(resultSQL)
        debug(f"o-o-o found {len(results)} result intervals")

        debug("o-o-o processing information about queries ...")
        resultsByQ = {}
        for (qid, first_m, last_m, qpub) in results:
            resultsByQ.setdefault(qid, []).append((first_m, last_m))
            pubStatus.setdefault(qid, {})[vr] = qpub == "T"
        debug(f"0-0-0 found {len(resultsByQ)} shared queries")

        for (qid, monads) in resultsByQ.items():
            chs = {}
            for (first_m, last_m) in monads:
                for m in range(first_m, last_m + 1):
                    thisCh = chFromM[m]
                    (ch_first_m, ch_last_m) = mFromCh[thisCh]
                    chs.setdefault(thisCh, []).append(
                        (max((first_m, ch_first_m)), min((last_m, ch_last_m)))
                    )
            chaptersFromQuery[qid] = list(chs)
            for (ch, monads) in chs.items():
                queriesFromChapter.setdefault(ch, {})[qid] = monads

        exe = time.time() - startTime
        debug(
            f"o-o-o making chapter-query index for version {vr} done in {exe} seconds"
        )
        return (queriesFromChapter, chaptersFromQuery)

    def updatePubStatus(self, vr, qid, isPublished):
        Caching = self.Caching

        debug(f"o-o-o updating pubStatus for query {qid} in version {vr} ...")
        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        pubStatus.setdefault(qid, {})[vr] = isPublished
        debug(f"o-o-o updating pubStatus for query {qid} in version {vr} done")

    def updateQCindex(self, vr, qid):
        Caching = self.Caching
        db = self.db

        debug(f"o-o-o updating chapter-query index for query {qid} in version {vr} ...")
        mFromCh = Caching.get(
            f"mFromCh_{vr}_",
            lambda: {},
            None,
        )
        chFromM = Caching.get(
            f"chFromM_{vr}_",
            lambda: {},
            None,
        )
        chaptersFromQuery = Caching.get(
            f"chaptersFromQuery_{vr}_",
            lambda: {},
            None,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            None,
        )
        # remove qid from both indexes: chaptersFromQuery and queriesFromChapter
        if qid in chaptersFromQuery:
            theseChapters = chaptersFromQuery[qid]
            for ch in theseChapters:
                if ch in queriesFromChapter:
                    if qid in queriesFromChapter[ch]:
                        del queriesFromChapter[ch][qid]
                    if not queriesFromChapter[ch]:
                        del queriesFromChapter[ch]
            del chaptersFromQuery[qid]

        # add qid again to both indexes (but now with updated results)
        resultSQL = f"""
select
    first_m, last_m
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and
    query_exe.executed_on >= query_exe.modified_on
inner join query on
    query.id = query_exe.query_id and query.is_shared = 'T'
where query_exe.query_id = {qid}
;
"""
        for (first_m, last_m) in db.executesql(resultSQL):
            chs = {}
            prevCh = None
            for m in range(first_m, last_m + 1):
                thisCh = chFromM[m]
                if prevCh != thisCh:
                    (ch_first_m, ch_last_m) = mFromCh[thisCh]
                    prevCh = thisCh
                chs.setdefault(thisCh, []).append(
                    (max((first_m, ch_first_m)), min((last_m, ch_last_m)))
                )
            if chs:
                chaptersFromQuery[qid] = list(chs)
                for (ch, monads) in chs.items():
                    queriesFromChapter.setdefault(ch, {})[qid] = monads
        debug(
            f"o-o-o updating chapter-query index for query {qid} in version {vr} done"
        )
