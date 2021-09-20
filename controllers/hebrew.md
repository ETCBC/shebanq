Note on caching

We use web2py caching for verse material and for item lists
(word lists and query lists).

see: http://web2py.com/books/default/chapter/29/04/the-core#cache

We also cache
- the list of bible books
- the table of all verse boundaries
- all the static pages.
We do not (yet) deliberately manage browser caching.
We use the lower-level mechanisms of web2py: cache.ram,
and refrain from decorating controllers with @cache or @cache.action,
because we have to be selective on which request vars are important
for keying the cached items.

We do not cache rendered views, because the views implement tweaks
that are dependent on the browser.
So we do not use response.render(result).

Note that what the user sees, is the effect of the javascript in hebrew.js
on the html produced by rendered view.
So the cached data only has to be indexed by those request vars that select content:
mr, qw, book, chapter, item id (iid) and (result) page.

I think this strikes a nice balance:
(a) these chunks of html are equal for all users that visit such a page,
    regardless of their view settings
(b) these chunks of html are relatively small, only the material of one page.

It is tempting to cache the SQL queries, but they fetch large amounts of data,
of which only a tiny portion shows up. So it uses a lot of space.
If a user examines a query with 1000 pages of results, it is unlikely
that she will visit all of them, so it is not worthwhile
to keep the results of the one big query in cache all the time.
On the other hand, many users look at the first page of query results,
and by caching individual pages, the number of times
that the big query is exececuted is reduced significantly.

Note on correctness:
If a user executes a query, the list of queries associated with a chapter
has to be recomputed for all chapters.
This means that ALL cached query lists of ALL chapters have to be cleared.
So if users are active with executing queries, the caching of query lists
is not very useful.
But for those periods where nobody executes a query,
all users benefit from better response times.
We cache in ram, but also on disk,
in order to retain the cache across restarting the webserver

Here are the cache keys we are using:

books_{vr}_                                   list of books plus fixed book info
blocks_{vr}_                                  list of 500w blocks plus boundary info
verse_boundaries                              for each verse its starting and ending
                                              slot (word number)
verses_{vr}_{mqwn}_{bk/iid}_{ch/page}_{tp}_   verses on a material page, either for a chapter,
                                              or an occurrences page of a lexeme,
                                              or a results page of a query execution
                                              or a page with notes by a user with a keyword
verse_{vr}_{bk}_{ch}_{vs}_                    a single verse in data representation
items_{qw}_{vr}_{bk}_{ch}_{pub}_              the items (queries or words)
                                              in a sidebar list of a page that shows a chapter
chart_{vr}_{qw}_{iid}_                        the chart data for a query or word
words_page_{vr}_{lan}_{letter}_               the data for a word index page
words_data_{vr}_                              the data for the main word index page


