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
        for (cid, first_m, last_m) in chapterList:
            for m in range(first_m, last_m + 1):
                chapterFromSlot[m] = cid
                slotsFromChapter[cid] = (first_m, last_m)
        resultSQL = f"""
select
    query_exe.query_id as query_id, first_m, last_m, query_exe.is_published
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
        for (query_id, first_m, last_m, is_published) in results:
            resultsByQ.setdefault(query_id, []).append((first_m, last_m))
            pubStatus.setdefault(query_id, {})[vr] = is_published == "T"
        debug(f"0-0-0 found {len(resultsByQ)} shared queries")

        for (query_id, slots) in resultsByQ.items():
            chs = {}
            for (first_m, last_m) in slots:
                for m in range(first_m, last_m + 1):
                    thisCh = chapterFromSlot[m]
                    (chapterFirstSlot, chapterLastSlot) = slotsFromChapter[thisCh]
                    chs.setdefault(thisCh, []).append(
                        (
                            max((first_m, chapterFirstSlot)),
                            min((last_m, chapterLastSlot)),
                        )
                    )
            chaptersFromQuery[query_id] = list(chs)
            for (ch, slots) in chs.items():
                queriesFromChapter.setdefault(ch, {})[query_id] = slots

        exe = time.time() - startTime
        debug(
            f"o-o-o making chapter-query index for version {vr} done in {exe} seconds"
        )
        return (queriesFromChapter, chaptersFromQuery)

    def updatePubStatus(self, vr, query_id, is_published):
        Caching = self.Caching

        debug(f"o-o-o updating pubStatus for query {query_id} in version {vr} ...")
        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            None,
        )
        pubStatus.setdefault(query_id, {})[vr] = is_published
        debug(f"o-o-o updating pubStatus for query {query_id} in version {vr} done")

    def updateQCindex(self, vr, query_id):
        Caching = self.Caching
        db = self.db

        debug(
            (
                f"o-o-o updating chapter-query index for query {query_id}"
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
        # remove query_id from both indexes: chaptersFromQuery and queriesFromChapter
        if query_id in chaptersFromQuery:
            theseChapters = chaptersFromQuery[query_id]
            for ch in theseChapters:
                if ch in queriesFromChapter:
                    if query_id in queriesFromChapter[ch]:
                        del queriesFromChapter[ch][query_id]
                    if not queriesFromChapter[ch]:
                        del queriesFromChapter[ch]
            del chaptersFromQuery[query_id]

        # add query_id again to both indexes (but now with updated results)
        resultSQL = f"""
select
    first_m, last_m
from monads
inner join query_exe on
    monads.query_exe_id = query_exe.id and query_exe.version = '{vr}' and
    query_exe.executed_on >= query_exe.modified_on
inner join query on
    query.id = query_exe.query_id and query.is_shared = 'T'
where query_exe.query_id = {query_id}
;
"""
        for (first_m, last_m) in db.executesql(resultSQL):
            chs = {}
            prevCh = None
            for m in range(first_m, last_m + 1):
                thisCh = chapterFromSlot[m]
                if prevCh != thisCh:
                    (chapterFirstSlot, chapterLastSlot) = slotsFromChapter[thisCh]
                    prevCh = thisCh
                chs.setdefault(thisCh, []).append(
                    (
                        max((first_m, chapterFirstSlot)),
                        min((last_m, chapterLastSlot)),
                    )
                )
            if chs:
                chaptersFromQuery[query_id] = list(chs)
                for (ch, slots) in chs.items():
                    queriesFromChapter.setdefault(ch, {})[query_id] = slots
        debug(
            (
                f"o-o-o updating chapter-query index for query {query_id}"
                f" in version {vr} done"
            )
        )
