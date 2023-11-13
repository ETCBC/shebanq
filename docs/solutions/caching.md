# Caching

We use caching to store material that is either frequently used or
expensive to compute.

We use [Web2py caching]({{web2pyCache}}).
We do not deliberately manage browser caching.
We use the lower-level mechanisms of Web2py: `cache.ram`,
and refrain from decorating controllers with `@cache` or `@cache.action`,
because we have to be selective on which request vars are important
for keying the cached items.

All caching is triggered via the [Model: CACHING][models.caching.CACHING] object.
We cache in RAM only, but there is a switch by which we could also cache on disk,
if we want to keep the cache between restarts of the server.

Here is a list of what we cache:

*   the numbers of chapters in each book
    [M: BOOKS.get][books.BOOKS.get]
*   heat maps (charts)
    [M: CHART.get][chart.CHART.get] and [M: CHART.getBlocks][chart.CHART.getBlocks]
*   chapter records
    [M: MATERIAL.getPassage][materials.MATERIAL.getPassage]
*   verse content (the content of verses that occur on a page)
    [M: MATERIAL.get][materials.MATERIAL.get]
*   single verse content in specific (re)presentation
    [M: VERSE.get][verse.VERSE.get] and
    [M: VERSE.getJson][verse.VERSE.getJson]
*   verse boundaries for a given set of slots, so that the pagination
    of result pages can be computed
    [M: MATERIAL.getPagination][materials.MATERIAL.getPagination]
*   notes occurrences
    [M: NOTE.read][note.NOTE.read]
*   clause atoms per verse
    [M: NOTE.getClauseAtoms][note.NOTE.getClauseAtoms]
    [M: NOTE.getClauseAtomFirstSlot][note.NOTE.getClauseAtomFirstSlot]
*   chapters per query and queries per chapter
    [M: QUERYCHAPTER.makeQCindex][querychapter.QUERYCHAPTER.makeQCindex] and
    [M: QUERYCHAPTER.updateQCindex][querychapter.QUERYCHAPTER.updateQCindex]
*   side material of pages
    [M: SIDE.get][side.SIDE.get]
*   definitions of view settings
    [M: VIEWDEFS][viewdefs.VIEWDEFS]
*   word pages
    [M: WORD.page][word.WORD.page]

We do not cache rendered views, because the views implement tweaks
that are dependent on the browser.

Note that what the user sees, is the effect of the javascript 
on the HTML produced by rendered view.
So the cached data only has to be indexed by those request vars that select content:
`mr`, `qw`, book, chapter, item `id` (`iid`) and (result) page.

I think this strikes a nice balance:
*   these chunks of HTML are equal for all users that visit such a page,
    regardless of their view settings
*   these chunks of HTML are relatively small, only the material of one page.

It is tempting to cache the SQL queries, but they fetch large amounts of data,
of which only a tiny portion shows up. So it uses a lot of space.
If a user examines a query with 1000 pages of results, it is unlikely
that (s)he will visit all of them, so it is not worthwhile
to keep the results of the one big query in cache all the time.
On the other hand, many users look at the first page of query results,
and by caching individual pages, the number of times
that the big query is executed is reduced significantly.

There is one exception: looking up the queries that have results in a given
chapter is quite expensive.
We alleviate that by making an index of queries by chapter and store that in the
cache.

!!! caution "Time consuming and priority"
    This is time consuming and it has to happen before the website is visited.
    If pages are served before this index is finished, sidebars maybe
    incomplete, and yet they will be cached, so they remain incomplete.

    The update script of SHEBANQ will make a first visit right after the update
    to counter this.

!!! note "Updating the index"
    When a query gets executed, it should be removed
    from the index and then added again.
    Therefore we need to know which chapters are affected.
    For that we also hold an index from queries to chapters
    in the cache.
