# Elements of the page

We give an overview of the elements of a typical shebanq page,
and we will name the different parts.
These concepts will recur in the discussion of the code,
whether it is Python, Javascript, CSS, HTML or SQL.

A good introduction into the kinds of pages is the menubar.

![menubar](../images/menubar.png)

## Main pages

Here is the

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

### Controls

![mcontrols](../images/materialcontrol.png) 
    
**text** page, above main area

*   *documentation*:

    a link to the documentation of the BHSA,
    where one can consult the ETCBC *features*,
    which is another name for their linguistic annotations.

*   *version*:

    switch between the available versions of the Hebrew Bible.
    Versions differ not so much in text content as well in the
    linguistic annotations. Supplying linguistic annotations
    is ongoing work for the ETCBC.

*   *language*:

    swithc between languages in which the names of
    the books of the bible are presented.

*   *text-presentation*
    *   select hebrew script or phonetic script

*   *tabbed-style*
    *   select normal running text, or one of several tabular formats.
        The tabular formats present the text by *clause atom*,
        one clause atom per line, with extra syntactic information added

        *   *Notes*: with notes displayed
        *   *Syntax*: with indentation according to linguistic embedding
        *   *Abstract*: with letter mapped to just a few symbols

**text-material** page only, above main area

*   *external links*:

    Each chapter has a link to the same chapter in other tools, such
    as [Bible Online Learner]({{bol}}) and [ParaBible]({{parabible}}).

*   *passage*:

    *   a book selector (click on Genesis to select from a list of books)
    *   a chapter selector (click on `1` to select from a list of chapters)

### Content

The main area presents a verse list.


