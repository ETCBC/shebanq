import time
from textwrap import dedent

from gluon import current

from constants import ALWAYS
from helpers import log, delta


class QUERYCHAPTER:
    def __init__(self):
        pass

    def makeQCindexes(self):
        VERSIONS = current.VERSIONS

        for vr in (
            ("2017", "2021") if current.SITUATION in {"local", "test"} else VERSIONS
        ):
            self.makeQCindex(vr)

    def makeQCindex(self, vr):
        """We build an index of queries by chapter in which they have results.

        The index building takes may take multiple seconds per data version.
        But the result is stored in the cache.

        We need to prevent that index-making is triggered multiple times by
        several requests that are fired while index-making is in progress.

        So we put an indicator value in the cache during index buidling,
        and we let everybody else wait until the index has been completed.

        We do this per version.

        To that end we put an empty dictionary in the cache.
        We only start computing the index key "busy" has a falsy value.
        Before computing the index, we set the value to 1.
        After computing the index, we set the value to 2.

        When the index is needed and the busy status is 1, we wait for it
        to become 2 before we continue.

        When the index is needed and busy is 2, the index has been
        built and we have to do nothing.

        Note that we do not need anything of the value of the index here,
        we only need it to be built, so that other parts of the app can get it
        quickly.

        We cannot allow that other parts of the app see an unfinished index,
        because it will lead to served content that is not yet correct.
        Because this content will be cached, it will take a long time (or forever)
        until it gets recomputed.
        """
        Caching = current.Caching

        busyStatus = Caching.get(f"busyIndex_{vr}_", lambda: {}, ALWAYS)
        busy = busyStatus.get("busy", 0)
        if busy == 0:
            busyStatus["busy"] = 1
            Caching.get(f"qcindex_{vr}_", lambda: self.makeQCindex_c(vr), ALWAYS)
            busyStatus["busy"] = 2
        elif busy == 1:
            n = 0
            while (
                Caching.get(f"busyIndex_{vr}_", lambda: {}, ALWAYS).get("busy", 0) == 1
            ):
                time.sleep(1)
                n += 1
                log(f"o-o-o waiting for chapter-query index {vr} ({n} sec) ...")

    def makeQCindex_c(self, vr):
        Caching = current.Caching
        db = current.db
        PASSAGE_DBS = current.PASSAGE_DBS

        log(f"o-o-o making chapter-query index for version {vr} ...")
        startTime = time.time()

        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            ALWAYS,
        )
        slotsFromChapter = Caching.get(
            f"slotsFromChapter_{vr}_",
            lambda: {},
            ALWAYS,
        )
        chapterFromSlot = Caching.get(
            f"chapterFromSlot_{vr}_",
            lambda: {},
            ALWAYS,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            ALWAYS,
        )
        chaptersFromQuery = Caching.get(
            f"chaptersFromQuery_{vr}_",
            lambda: {},
            ALWAYS,
        )

        chapterSQL = dedent(
            """
            select id, first_m, last_m from chapter
            ;
            """
        )
        chapterList = PASSAGE_DBS[vr].executesql(chapterSQL)
        for (chapter_id, first_m, last_m) in chapterList:
            for m in range(first_m, last_m + 1):
                chapterFromSlot[m] = chapter_id
                slotsFromChapter[chapter_id] = last_m
        resultSQL1 = dedent(
            f"""
            select
                query_exe.id, query_exe.is_published, query.id
            from query
            inner join query_exe on
                query.id = query_exe.query_id
            where
                query_exe.version = '{vr}'
            and
                query_exe.executed_on >= query_exe.modified_on
            and
                query.is_shared = 'T'
            ;
            """
        )

        queryTime = time.time()
        results1 = db.executesql(resultSQL1)
        queryTime = time.time() - queryTime
        log(f"      found {len(results1)} shared queries in {delta(queryTime)}")

        queryFromExe = {}
        for (query_exe_id, is_published, query_id) in results1:
            queryFromExe[query_exe_id] = query_id
            pubStatus.setdefault(query_id, {})[vr] = is_published == "T"

        if queryFromExe:
            doQueryIndex(db, vr, queryFromExe)

        exe = time.time() - startTime
        log(f"o-o-o made chapter-query index for data {vr} in {delta(exe)}")
        return (queriesFromChapter, chaptersFromQuery)

    def updatePubStatus(self, vr, query_id, is_published):
        Caching = current.Caching

        log(f"o-o-o updating pubStatus for query {query_id} in version {vr} ...")
        pubStatus = Caching.get(
            f"pubStatus_{vr}_",
            lambda: {},
            ALWAYS,
        )
        pubStatus.setdefault(query_id, {})[vr] = is_published
        log(f"o-o-o updating pubStatus for query {query_id} in version {vr} done")

    def updateQCindex(self, vr, query_id, uptodate=True):
        """Update the chapter-query index if a query has been run or rerun.

        We want an up to date mapping from chapters to the shared, up-to-date
        queries with results in those chapters.

        We call this function when:
        *   a query has run and a niew set of slots has been stored.
        *   the sharing status of a query changes

        We do not call this function when:
        *   the published state of a query has changed (see updatePubStatus)
        *   when a query body is edited but not run (see below).

        In those cases the following will be taken care of:

        First delete the query from the index.
        If the query is shared and up to date, we add it back to the index
        based on its results.

        However, this function might be called at a time that the results
        of the query have been stored in the database, before the metadata
        has arrived there.
        In that case we can not test on the uptodateness, so we assume that the
        caller has passed uptodate=True.
        Indeed, when the sharing status has changed, we are able to perform
        this test, and then there is no need to pass uptodate=True.


        What if a query body is edited but not run? It will then become outdated,
        and should be removed from the index.
        But that is a rather costly operation, and it is likely that a query is edited
        many times before it is run again.
        What we do instead is, that when we fetch queries for the sidebar of a chapter,
        we skip the ones that are outdated.
        """
        Caching = current.Caching
        db = current.db

        log((f"o-o-o updating chapter-query index for data {vr}"))
        startTime = time.time()

        chaptersFromQuery = Caching.get(
            f"chaptersFromQuery_{vr}_",
            lambda: {},
            ALWAYS,
        )
        queriesFromChapter = Caching.get(
            f"queriesFromChapter_{vr}_",
            lambda: {},
            ALWAYS,
        )
        # remove query_id from both indexes: chaptersFromQuery and queriesFromChapter
        if query_id in chaptersFromQuery:
            theseChapters = chaptersFromQuery[query_id]
            for chapter_id in theseChapters:
                if chapter_id in queriesFromChapter:
                    if query_id in queriesFromChapter[chapter_id]:
                        del queriesFromChapter[chapter_id][query_id]
                    if not queriesFromChapter[chapter_id]:
                        del queriesFromChapter[chapter_id]
            del chaptersFromQuery[query_id]

        # add query_id again to both indexes (but now with updated results)
        uptodateSQL = (
            ""
            if uptodate
            else dedent(
                """
                and
                    query_exe.executed_on >= query_exe.modified_on
                """
            )
        )
        resultSQL1 = dedent(
            f"""
            select
                query_exe.id, query.id
            from query
            inner join query_exe on
                query.id = query_exe.query_id
            where
                query.id = {query_id}
            and
                query_exe.version = '{vr}'
            and
                query.is_shared = 'T'
            {uptodateSQL}
            ;
            """
        )
        queryTime = time.time()
        results1 = db.executesql(resultSQL1)
        queryTime = time.time() - queryTime
        log(f"      found {len(results1)} shared queries in {delta(queryTime)}")

        queryFromExe = {}
        for (query_exe_id, query_id) in results1:
            queryFromExe[query_exe_id] = query_id

        if queryFromExe:
            doQueryIndex(db, vr, queryFromExe)

        exe = time.time() - startTime
        log(f"o-o-o updated chapter-query index for data {vr} in {delta(exe)}")


def doQueryIndex(db, vr, queryFromExe):
    Caching = current.Caching

    slotsFromChapter = Caching.get(f"slotsFromChapter_{vr}_", lambda: {}, ALWAYS)
    chapterFromSlot = Caching.get(f"chapterFromSlot_{vr}_", lambda: {}, ALWAYS)
    chaptersFromQuery = Caching.get(f"chaptersFromQuery_{vr}_", lambda: {}, ALWAYS)
    queriesFromChapter = Caching.get(f"queriesFromChapter_{vr}_", lambda: {}, ALWAYS)

    resultSQL2 = dedent(
        f"""
        select query_exe_id, first_m, last_m from monads
        where
        query_exe_id in ({",".join(str(idx) for idx in queryFromExe)})
        ;
        """
    )
    queryTime = time.time()
    results2 = db.executesql(resultSQL2)
    queryTime = time.time() - queryTime
    log(f"      found {len(results2)} result intervals in {delta(queryTime)}")

    log("      processing information about queries ...")
    procTime = time.time()

    resultsByQ = {}
    for (query_exe_id, first_m, last_m) in results2:
        query_id = queryFromExe[query_exe_id]
        resultsByQ.setdefault(query_id, []).append((first_m, last_m))
    log(f"      found {len(resultsByQ)} shared queries")

    for (query_id, ranges) in resultsByQ.items():
        chapters = {}
        for (first_m, last_m) in ranges:
            if first_m == last_m:
                chapter_id = chapterFromSlot[first_m]
                chapters.setdefault(chapter_id, []).append((first_m, first_m))
                continue

            m = first_m
            while m <= last_m:
                chapter_id = chapterFromSlot[m]
                chapterLastSlot = slotsFromChapter[chapter_id]
                endM = min((last_m, chapterLastSlot))
                chapters.setdefault(chapter_id, []).append((m, endM))
                m = chapterLastSlot + 1

        if chapters:
            chaptersFromQuery[query_id] = list(chapters)
            for (chapter_id, ranges) in chapters.items():
                queriesFromChapter.setdefault(chapter_id, {})[query_id] = ranges

    procTime = time.time() - procTime
    log(f"      processed shared queries into index in {delta(procTime)}")
