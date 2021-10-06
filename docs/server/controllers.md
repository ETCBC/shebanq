# Controllers

The controllers can be grouped as follows.

## Default controllers

In *default.py*.

### `index()`

This is used for getting the home page.

## Feed controllers

In *feed.py*.

### `atom()`

This is used to provide a list with recently saved shared queries.

## Hebrew controllers

In *hebrew.py*.

The significant controllers are all here.
Their bodies are very short, because they all
call a function from the modules, which does all the work.

### Toplevel

Controllers that correspond to the menu items in the navigation bar.

#### `text()`

Produces the skeleton of a text page.

Calls 

::: viewsettings.VIEWSETTINGS.page

### `words()`

Produces the lexicon overview page.

Calls

::: word.WORD.page
