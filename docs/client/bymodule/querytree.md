<a name="module_querytree"></a>

## querytree

* [querytree](#module_querytree)
    * [~View](#module_querytree..View)
    * [~Level](#module_querytree..Level)
    * [~Filter](#module_querytree..Filter)
    * [~Tree](#module_querytree..Tree)
        * [new Tree()](#new_module_querytree..Tree_new)
        * [.record()](#module_querytree..Tree+record)
    * [~subtractForQueriesPage](#module_querytree..subtractForQueriesPage)
    * [~controlHeight](#module_querytree..controlHeight)

<a name="module_querytree..View"></a>

### querytree~View
Advanced or simple view of the tree of queries.
In advanced views there are more sophisticated counts.

**Kind**: inner class of [<code>querytree</code>](#module_querytree)  
<a name="module_querytree..Level"></a>

### querytree~Level
The tree can be shown at different levels:

*   organization
*   project
*   user
*   query

**Kind**: inner class of [<code>querytree</code>](#module_querytree)  
<a name="module_querytree..Filter"></a>

### querytree~Filter
The tree can be filtered.

This is a full text search on the texts of the nodes.

**Kind**: inner class of [<code>querytree</code>](#module_querytree)  
<a name="module_querytree..Tree"></a>

### querytree~Tree
Handles the tree of queries

**Kind**: inner class of [<code>querytree</code>](#module_querytree)  
**See**: Triggers [C:hebrew.querytree][controllers.hebrew.querytree]  

* [~Tree](#module_querytree..Tree)
    * [new Tree()](#new_module_querytree..Tree_new)
    * [.record()](#module_querytree..Tree+record)

<a name="new_module_querytree..Tree_new"></a>

#### new Tree()
Initializes the query tree

Stores a URL to fetch content from the server.

<a name="module_querytree..Tree+record"></a>

#### tree.record()
Sends a record to the database to be saved

**Kind**: instance method of [<code>Tree</code>](#module_querytree..Tree)  
**See**: Triggers [C:hebrew.itemrecord][controllers.hebrew.itemrecord]  
<a name="module_querytree..subtractForQueriesPage"></a>

### querytree~subtractForQueriesPage
the canvas holding the material gets a height equal to
the window height minus this amount

**Kind**: inner constant of [<code>querytree</code>](#module_querytree)  
<a name="module_querytree..controlHeight"></a>

### querytree~controlHeight
height for messages and controls

**Kind**: inner constant of [<code>querytree</code>](#module_querytree)  
