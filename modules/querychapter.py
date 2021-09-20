import time

from helpers import debug


class QUERYCHAPTER:
    def __init__(self, Caching, db, PASSAGE_DBS):
        self.Caching = Caching

    def makeQCindex(self, vr):
        Caching = self.Caching

        Caching.get(f"qcindex_{vr}_", lambda: self.makeQCindex_c(vr), None)

    def makeQCindex_c(self, vr):
        Caching = self.Caching
        db = self.db
        PASSAGE_DBS = self.PASSAGE_DBS

        debug(f"o-o-o making chapter-query index for version {vr} ...")
        startTime = time.time()

        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        slotsFromChapter = Caching.get(
            f"mFromCh_{vr}_",
            lambda: {},
            None,
        )
        chapterFromSlot = Caching.get(
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
        chapterList = PASSAGE_DBS[vr].executesql(chapterSQL)
        for (cid, firstSlot, lastSlot) in chapterList:
            for m in range(firstSlot, lastSlot + 1):
                chapterFromSlot[m] = cid
                slotsFromChapter[cid] = (firstSlot, lastSlot)
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
        for (queryId, firstSlot, lastSlot, qpub) in results:
            resultsByQ.setdefault(queryId, []).append((firstSlot, lastSlot))
            pubStatus.setdefault(queryId, {})[vr] = qpub == "T"
        debug(f"0-0-0 found {len(resultsByQ)} shared queries")

        for (queryId, slots) in resultsByQ.items():
            chs = {}
            for (firstSlot, lastSlot) in slots:
                for m in range(firstSlot, lastSlot + 1):
                    thisCh = chapterFromSlot[m]
                    (chapterFirstSlot, chapterLastSlot) = slotsFromChapter[thisCh]
                    chs.setdefault(thisCh, []).append(
                        (
                            max((firstSlot, chapterFirstSlot)),
                            min((lastSlot, chapterLastSlot)),
                        )
                    )
            chaptersFromQuery[queryId] = list(chs)
            for (ch, slots) in chs.items():
                queriesFromChapter.setdefault(ch, {})[queryId] = slots

        exe = time.time() - startTime
        debug(
            f"o-o-o making chapter-query index for version {vr} done in {exe} seconds"
        )
        return (queriesFromChapter, chaptersFromQuery)

    def updatePubStatus(self, vr, queryId, isPublished):
        Caching = self.Caching

        debug(f"o-o-o updating pubStatus for query {queryId} in version {vr} ...")
        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        pubStatus.setdefault(queryId, {})[vr] = isPublished
        debug(f"o-o-o updating pubStatus for query {queryId} in version {vr} done")

    def updateQCindex(self, vr, queryId):
        Caching = self.Caching
        db = self.db

        debug(
            (
                f"o-o-o updating chapter-query index for query {queryId}"
                f" in version {vr} ..."
            )
        )
        slotsFromChapter = Caching.get(
            f"mFromCh_{vr}_",
            lambda: {},
            None,
        )
        chapterFromSlot = Caching.get(
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
        # remove queryId from both indexes: chaptersFromQuery and queriesFromChapter
        if queryId in chaptersFromQuery:
            theseChapters = chaptersFromQuery[queryId]
            for ch in theseChapters:
                if ch in queriesFromChapter:
                    if queryId in queriesFromChapter[ch]:
                        del queriesFromChapter[ch][queryId]
                    if not queriesFromChapter[ch]:
                        del queriesFromChapter[ch]
            del chaptersFromQuery[queryId]

        # add queryId again to both indexes (but now with updated results)
        resultSQL = f"""
select
    first_m, last_m
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and
    query_exe.executed_on >= query_exe.modified_on
inner join query on
    query.id = query_exe.query_id and query.is_shared = 'T'
where query_exe.query_id = {queryId}
;
"""
        for (firstSlot, lastSlot) in db.executesql(resultSQL):
            chs = {}
            prevCh = None
            for m in range(firstSlot, lastSlot + 1):
                thisCh = chapterFromSlot[m]
                if prevCh != thisCh:
                    (chapterFirstSlot, chapterLastSlot) = slotsFromChapter[thisCh]
                    prevCh = thisCh
                chs.setdefault(thisCh, []).append(
                    (
                        max((firstSlot, chapterFirstSlot)),
                        min((lastSlot, chapterLastSlot)),
                    )
                )
            if chs:
                chaptersFromQuery[queryId] = list(chs)
                for (ch, slots) in chs.items():
                    queriesFromChapter.setdefault(ch, {})[queryId] = slots
        debug(
            (
                f"o-o-o updating chapter-query index for query {queryId}"
                f" in version {vr} done"
            )
        )
