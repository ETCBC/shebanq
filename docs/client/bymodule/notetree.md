<a name="module_notetree"></a>

## notetree

* [notetree](#module_notetree)
    * [~View](#module_notetree..View)
    * [~Level](#module_notetree..Level)
    * [~Filter](#module_notetree..Filter)
    * [~Tree](#module_notetree..Tree)
        * [new Tree()](#new_module_notetree..Tree_new)
    * [~Upload](#module_notetree..Upload)
        * [.submit()](#module_notetree..Upload+submit)
    * [~subtractForNotesPage](#module_notetree..subtractForNotesPage)

<a name="module_notetree..View"></a>

### notetree~View
Advanced or simple view of the tree of notes.
In advanced views there are more sophisticated counts.

**Kind**: inner class of [<code>notetree</code>](#module_notetree)  
<a name="module_notetree..Level"></a>

### notetree~Level
The tree can be shown at different levels:

*   user
*   note set

**Kind**: inner class of [<code>notetree</code>](#module_notetree)  
<a name="module_notetree..Filter"></a>

### notetree~Filter
The tree can be filtered.

This is a full text search on the texts of the nodes.

**Kind**: inner class of [<code>notetree</code>](#module_notetree)  
<a name="module_notetree..Tree"></a>

### notetree~Tree
Handles the tree of note sets

**Kind**: inner class of [<code>notetree</code>](#module_notetree)  
**See**: Triggers [C:hebrew.notetree][controllers.hebrew.notetree]  
<a name="new_module_notetree..Tree_new"></a>

#### new Tree()
Initializes the notes tree

Stores a URL to fetch content from the server.

<a name="module_notetree..Upload"></a>

### notetree~Upload
Controls the bulk-uploading of notes

**Kind**: inner class of [<code>notetree</code>](#module_notetree)  
<a name="module_notetree..Upload+submit"></a>

#### upload.submit()
Submits a CSV file with notes to the server

**Kind**: instance method of [<code>Upload</code>](#module_notetree..Upload)  
**See**: Triggers [C:hebrew.noteupload][controllers.hebrew.noteupload].  
<a name="module_notetree..subtractForNotesPage"></a>

### notetree~subtractForNotesPage
the canvas holding the material gets a height equal to
the window height minus this amount

**Kind**: inner constant of [<code>notetree</code>](#module_notetree)  
