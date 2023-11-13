# Application workflow:

There is a skeleton page, which has a main area and a left sidebar.
The skeleton is filled with static HTML, with certain div elements in it that
will be filled on demand by means of ajax calls.

An actual page is composed by selectively showing and hiding parts of the
skeleton and by filling div elements through ajax calls.

A page is represented by a javascript object with data and methods.

There are two kinds of pages:

*   `m`: material (showing verses of a chapter)
*   `r`: results  (showing verses of a result page)

An `m`-page has different sidebars than an `r`-page.

The skeleton has the following parts:

*   Sidebar with
    *   `m-w`: `ViewSettings` plus a list of word items
    *   `m-q`: `ViewSettings` plus a list of query items
    *   `r-w`: `ViewSettings` plus the metadata of an individual word
    *   `r-q`: `ViewSettings` plus the metadata of an individual query

*   Main part with
    *   heading
    *   material selector (`m`: book/chapter, `r`: result pages)
    *   settings (text/data selector)
    *   material (either the verses of a passage or the verses of the
        result page of a query or word)
    *   share link

There is a `viewstate`, an object that maintains the `ViewSettings` that can be
modified by the user.
The `viewstate` object is a member of the page object.
`viewstate` is divided in groups, each group is serialized to a cookie.
`viewstate` is initialized from the query string and/or the cookies.
When query string and cookie conflict, the query string wins.
Whenever a user clicks, the `viewstate` is changed and immediately saved in the
corresponding cookie.

Depending on user actions, parts of the skeleton are loaded with HTML, through
AJAX calls with methods that perform actions when the data has been loaded.

The application goes through the following stages:

*   **init functions**
    Decorate the fixed parts of the skeleton with JQUERY actions.
    Do not change the `viewstate`, do not look at the `viewstate`.

*   **click functions (events)**
    Change the `viewstate` in response to user actions.

*   **apply functions**
    Look at the `viewstate` and adapt the display of the page, this might entail
    ajax actions.
    Do not change the `viewstate`.

*   **process functions**
    Very much like init functions, but only for content that has been loaded
    through later AJAX calls.

The cookies are:

*   *`material`*
    the current book, chapter, result page, item id,
    *   `qw` (`q`=query, `w`=word, tells whether the item in question is a
        query or a word),
    *   `mr` (`m`=material, `r`=result of query or word search, corresponds to the two
        kinds of pages),
    *   `tp` (text-or-tab setting: whether the material is shown as
        plain text (`txtp`) or as tabbed text in several versions (`txt1`, `txt2`, etc.)
        there is also `txtd` for interlinear data, but that is on demand per verse
    *   `tr` (script or phonetic setting: whether the hebrew text is rendered
        in hebrew script or phonetically)
    *   `lang` (language choice for the book names)

*   *`hebrewdata`*
    a list of switches controlling which fields are shown in the interlinear data view

*   *`highlights`*
    groups of settings controlling the highlight colours
    *   group `q`: for queries
    *   group `w`: for words

    Both groups contain the same settings:
    *   `active` (which is the active setting: `hloff`, `hlone`, `hlcustom`, `hlmany`)
    *   `sel_one` (the colour if all queries/words are highlighted with one colour)
    *   `get` (whether or not to retrieve the side list of relevant items)

*   *`colormap`*
    mappings between queries and colours (`q`) and between words and colours (`w`),
    based on the id of queries and words

## Window layout

All variable content is placed in div elements with fixed height and scroll bars.
So the contents of sidebars and main area can be scrolled independently.
So the main parts of the page are always in view, at fairly stable places.

When editing a query it is important to make room for the query body.
When editing is happening, the sidebar will be widened at the expense of the main area.

Plans for the near future:

*   **Done** Load data view per verse, not per chapter. A click on the verse
    number should be the trigger.

*   **Done** Make SHEBANQ able to deal with several versions of the data.
    Queries will get an execution record per version of the data.

Plans for distant future:

I. integrate the Queries page with this page.

The skeleton will have 4 columns, of which 2 or three are visible at a given time:

*   A: filter and level controls for the queries tree
*   B: the queries tree itself
*   C: an individual query, possibly in edit mode, or an individual word
*   D: material column: the verses of a chapter, or a page with occurrences of
    a word, or a page with query results

Then the hebrew.js and the querytree.js can be integrated, redundant code can
be erased, ajax messages can be done more consistently.

II. replace all usage of cookies by local storage.

The queries page already does not use cookies but local storage.
Now the parsing of the request.vars occurs server side in Python, maybe it is
better to defer all checks to the browser.
The browser can then keep all view settings to its own, without any need to
communicate view settings with the server.

III. send all data from server to browser in JSON form.

The browser generates HTML out of the JSON.
I am not sure whether this is worth it.
On the one hand it means smaller data transfers (but they are already fast
enough), on the other hand, template code in python is
much more manageable than in Javascript.

# Sidebars

The main material can be two kinds (`mr`)

*   `m` = material: chapters from books
*   `r` = query/word results

There are four kinds of sidebars, indicated by two letters,
of which the first indicates the `mr`:

*   `mq` = list of queries relevant to main material
*   `mw` = list of words relevant to main material
*   `rq` = display of query record, the main material are the query results
*   `rw` = display of word record, the main material are the word results

The list sidebars (`m`) have a colour picker for selecting a uniform highlight colour,
plus controls for deciding whether no, uniform, custom, or many colours will be used.

The record-side bars (`r`) only have a single colour picker, for
choosing the colour associated with the item (a query or a word).

When items are displayed in the list sidebars, they each have a colour picker that
is identical to the one used for that item in the record sidebar.

The colour pickers for choosing an associated item colour, consist of a
checkbox and a proper `colorpicker`.
The checkbox indicates whether the colour is customized.
A colour gets customized when the user selects an other colour than the default
one, or by checking the box.

When the user has chosen custom colours, all highlights will be done with the
uniform colour, except the customized ones.

Queries are highlighted by background colour, words by foreground colours.
Although the names for background and foreground colours are identical, their
actual values are not.
Foreground colours are darkened, background colours are lightened.
This is done for better visibility.

All colour associations are preserved in cookies, one for queries, and one for words.
Nowhere else are they stored, but they can be exported as a (long) link.
By using the share link, the user can preserve colour settings in a notebook,
or mail them to colleagues.
