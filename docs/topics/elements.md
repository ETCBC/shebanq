# Elements of the page

We give an overview of the elements of a typical shebanq page,
and we will name the different parts.
These concepts will recur in the discussion of the code,
whether it is Python, Javascript, CSS, HTML or SQL.

A good introduction into the kinds of pages is the menubar.

![menubar](../images/menubar.png)

## Main pages

There are several kinds of main pages

*   **text** pages have Hebrew text material
*   **words** presents the lexicon
*   **queries** presents the family of saved queries,
    organized by organization, project and user
*   **notes** presents the family of saved notes,
    organized by organization, project and user

The **text** pages are the bread and butter of shebanq,
they are subdivided into two kinds:

*   **material** pages show a chapter of the Hebrew Bible:
    *   the left sidebar may show related words, queries, notes
    *   the main area shows the text of the chapter,
        as a list of its verses;

*   **record** pages show an individual *word*, *query*, or *note set*;
    we use the term *record* to refer to an individual word, query or
    note set.
    *   the left sidebar shows the characteristics of the
        record, depending on the type of the record,
    *   the main area shows the verses that belong to that record,
        as a list of verses, being:
        *   for a word, the verses where it occurs;
        *   for a query, shows the verses where it has results;
        *   for a note set, the verses where it has members.

## Text pages in detail

All text pages have a left side bar and a main area.
Both areas have a header which contains verious controls
that influence the selection and presentation of the content.

Here is a schematic overview.

```
===============================================================================
|all: icon menu                                                         login |
|all:      Text Word Queries Notes                                            |
===============================================================================

======================    =====================================================
|m:w list controls   |    |m:  material controls   book chapter               |
|m:w word list       |    |m:  verse content                            verse |
|m:w                 |    |m:  verse content                            verse |
----------------------    |m:  verse content                            verse |
|m:q list controls   |    =====================================================
|m:q query list      |    |rw: material controls   word page                  |
|m:q query list      |    |rw: verse content                    chapter:verse |
|m:q                 |    |rw: verse content                            verse |
----------------------    |rw: verse content                            verse |
|m:n list controls   |    =====================================================
|m:n note list       |    |rq: material controls   query page                 |
|m:n                 |    |rq: verse content                            verse |
======================    |rq: verse content                            verse |
|rw: record control  |    |rq: verse content                            verse |
|rw: word info       |    =====================================================
|rw:                 |    |rn: material controls   noteset page               |
======================    |rn: verse content                            verse |
|rq: record control  |    |rn: verse content                            verse |
|rq: query info      |    |rn: verse content                            verse |
|rq:                 |    =====================================================
======================
|rn: record control  |
|rn: note set info   |                                            =============
|rn:                 |                                            |text: cite |
======================                                            =============
```

Not all blocks occur on all pages. The *qualifiers* indicate what occurs on what:

qualifier | page type
--- | ---
`all:` | all pages
`text:` | all *text* pages
`m:` | all material *text* pages
`m:w` | all material *text* pages if word sidebar is on
`m:q` | all material *text* pages if query sidebar is on
`m:n` | all material *text* pages if noteset sidebar is on
`rw:` | all record *text* pages of type word
`rq:` | all record *text* pages of type query
`rn:` | all record *text* pages of type noteset

### Operation

When a SHEBANQ user navigates on a text page, he can switch between
`m` and `r` pages.

On an `m` page he sees chapter material, in a sidebar he sees lists of
related words, queries, notes.

A click on a related query item opens an `rq` page.

There he sees hits of that query.
Every hit has a link to the chapter the hit is in.
A click on that chapter opens an `m` page for that chapter.

In the sidebars there are again related words, queries, notes.

A click on a related word opens an `rw` page.

And so on.

Under the hood there is just a single page.

All blocks are always present on a text page, but not all are visible.
Two parameters regulate which one are visible

*   *mr* = `m` or `r`
*   *qw* = `w` or `q` or `n`

Changes in *mr* and *qw* trigger the showing and hiding of the appropriate
blocks.
Moreover, if needed, fresh content for these blocks is fetched
from the server by means of AJAX calls and inserted into them.

So, during all this navigation, the skeleton of the page does not
change, and the server is only accessed by for partial content.

### Material Controls

![materialcontrols](../images/materialcontrol.png) 
    
#### info
![info](../images/elem_info.png)
link to feature docs of BHSA

code type | associated names
--- | ---
CSS |`source.ctli`
JS | `select.SelectPassage`
views | versions.html |
modules | --
controllers | --

#### version
![version](../images/elem_version.png)
select ETCBC data version

code type | associated names
--- | ---
CSS | `mvradio.ctl`
JS | `words.View.init`, `select.SelectPassage.apply`
views | versions.html
modules | `ViewSettings`

#### language
![language](../images/elem_language.png)
switch between languages in which the names of
the books of the bible are presented.

code type | associated names
--- | ---
CSS | `#thelang`, `#select_control_lang`
JS | `select.SelectLangugae`
views | textbody.html
modules | blang.py

#### text representation
![tr](../images/elem_tr.png)
select hebrew script or phonetic script

code type | associated names
--- | ---
CSS | `mtradio.ctl`, `mhb`, `mph`
JS | `tr`, `materialsettings.MaterialSettings`
views | textbody.html
modules | `tr`, `VerseContent.plainText`

#### text presentation
![tp](../images/elem_tp.png)
select normal running text, or one of several tabular formats.
The tabular formats present the text by *clause atom*,
one clause atom per line, with extra syntactic information added

*   *Notes*: with notes displayed
*   *Syntax*: with indentation according to linguistic embedding
*   *Abstract*: with letter mapped to just a few symbols

code type | associated names
--- | ---
CSS | `mhradio.ctl`, `#mtxtp`. `mtxt1`, `#mtxt2`, `mtxt3`
JS | `tp`, `materialsettings.MaterialSettings`, `select.SelectPassage`
views | textbody.html
modules | `tp`, `VerseContent.material`

#### book
![book](../images/elem_book.png)
select a book of the bible, not on **record** pages

code type | associated names
--- | ---
CSS | `#select_control_book`, `#thebook`
JS | `book`, `material.Material`, `select.SelectBook/SelectPassage`, `share.`
views | textbody.html
modules | `book`, `materials.MATERIAL`, `book`, `books.BOOKS`

#### chapter
![chapter](../images/elem_chapter.png)
select a chapter within the current book, not on **record** pages,
with controls to go to next/previous chapters

code type | associated names
--- | ---
CSS | `#select_control_chapter`, `#thechapter`
JS | `chapter`, `material.Material`, `select.SelectItems/SelectPassage`, `share.`
views | textbody.html
modules | `chapter`, `materials.MATERIAL`, `book`, `books.BOOKS`

#### page
![page](../images/elem_page.png)
select a page within the list of items associated with
the current record (word/query/note set), not on **material** pages,
with controls to go to next/previous pages

code type | associated names
--- | ---
CSS | `#select_control_page`, `#thepage`
JS | `page`, `material.Material`, `select.SelectItems`, `share.`
views | textbody.html
modules | `page`, `materials.MATERIAL`

#### links
![links](../images/elem_links.png)
each chapter has a link to the same chapter in other tools, such
as [Bible Online Learner]({{bol}}) and [ParaBible]({{parabible}}),
not on **record** pages.

code type | associated names
--- | ---
CSS | `#bol_lnk`, `#pbl_lnk`
JS | `select.SelectPassage`
views | textbody.html

### List Controls

![listcontrols](../images/listcontrol.png) 
    
#### highlight published
![hlpublished](../images/elem_hlpublished.png)
show published items only;
not in **word** item lists

code type | associated names
--- | ---
CSS | `#hlpub[qn]`, `[qn]pradio.ctl`
JS | `sideSettings.SideSettings`, `notes.NoteVerse`
views | textsidebar.html
modules | `viewdefs.Make`

#### highlight reset
![hlreser](../images/elem_hlreset.png)
reset the highlighting of all items in this list;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#hlreset[wq]`, `[wq]hradio.ctl`
JS | `sideSettings.SideSettings`, `page.Page`
views | textsidebar.html
modules | `viewdefs.Make`

#### highlight many
![hlmany](../images/elem_hlmany.png)
highlight all items in this list;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#hlmany[wq]`, `[wq]hradio.ctl`
JS | `sideSettings.SideSettings`, `page.Page`
views | textsidebar.html
modules | `viewdefs.Make`

#### highlight custom
![hlcustom](../images/elem_hlcustom.png)
highlight only selected items in this list;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#hlcustom[wq]`, `[wq]hradio.ctl`
JS | `sideSettings.SideSettings`, `page.Page`
views | textsidebar.html
modules | `viewdefs.Make`

#### highlight one
![hlone](../images/elem_hlone.png)
highlight the selected items in this list 
and use only one color for that,
to be selected in the box next to it;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#hlone[wq]`, `[wq]hradio.ctl`
JS | `sideSettings.SideSettings`, `page.Page`
views | textsidebar.html
modules | `viewdefs.Make`

#### highlight off
![hloff](../images/elem_hloff.png)
turn highlighting off for all items in this list ;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#hloff[wq]`, `[wq]hradio.ctl`
JS | `sideSettings.SideSettings`, `page.Page`
views | textsidebar.html
modules | `viewdefs.Make`

#### select single highlight color
![hlselect](../images/elem_hlselect.png)
if **highlight one** is chosen,
pick the color used for all highlights;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#sel[wq]_one`, `colorselect_[wq]`
JS | `sideSettings.SideSettings`, `page.Page`, `colorpicker.ColorPicker1/ColorPicker2`, `viewState.viewState`
views | textsidebar.html
modules | `viewdefs.Make`

### Record Control

#### select highlight color
![hlrselect](../images/elem_hlrselect.png)
pick the color used to highlight items of this record,
i.e. occurrences of this word or hits of this query;
not in **note** item lists

code type | associated names
--- | ---
CSS | `#sel[wq]_me`, `colorselect_[wq]`
JS | `sideSettings.SideSettings`, `page.Page`, `colorpicker.ColorPicker1/ColorPicker2`, `viewState.viewState`
views | textsidebar.html
modules | `viewdefs.Make`


### Content

The main area presents a verse list.
The verses are those of a chapter for an `m` page, and those of a record for an `r` page.
Think of query results and word occurrences and notes from a note set.

#### goto chapter
![chapterverse](../images/elem_chapterverse.png)

`r` pages show book-chapter indications next to the verses,
which link to the `m` pages of the corresponding book chapters.

code type | associated names
--- | ---
CSS | `cref`
JS | `material.Material`
views | material.html

#### show verse data
![chapterverse](../images/elem_versedata.png)

Both `m` and `r` pages show verse numbers next to the verses,
which are clickable and open a data view of the corresponding verses,
together with a legend button.

code type | associated names
--- | ---
CSS | `vradio`, `#datalegend_control`
JS | `material.Material`
views | material.html

#### feature legend
![legend](../images/elem_legend.png)

The legend can be used to control which features are displayed in data view.
The feature labels in the legend link to the feature documentation
in the [BHSA]({{bhsa}}) repo.

code type | associated names
--- | ---
CSS | `#datalegend_control`
JS | `material.Material`, `materialsettings.MaterialSettings`
views | textbody.html, material.html
