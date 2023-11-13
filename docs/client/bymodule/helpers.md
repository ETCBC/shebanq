<a name="module_helpers"></a>

## helpers

* [helpers](#module_helpers)
    * `static`
        * [.escHT](#module_helpers.escHT)
        * [.putMarkdown](#module_helpers.putMarkdown)
        * [.toggleDetail](#module_helpers.toggleDetail)
        * [.specialLinks](#module_helpers.specialLinks)
        * [.colorDefault](#module_helpers.colorDefault)
        * [.closeDialog](#module_helpers.closeDialog)
    * `inner`
        * [~mEscape()](#module_helpers..mEscape)

<a name="module_helpers.escHT"></a>

### helpers.escHT
Escape the `&` `<` `>` in strings that must be rendered as HTML.

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  
<a name="module_helpers.putMarkdown"></a>

### helpers.putMarkdown
Display markdown

The markdown is formatted as HTML, where shebanq-specific links
are resolved into working hyperlinks.

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  

| Parameter | Description |
| --- | --- |
| `wdg` | A div in the HTML This div has a sub-div with the source markdown in it
and a destination div which gets the result of the conversion |

<a name="module_helpers.toggleDetail"></a>

### helpers.toggleDetail
Hide and expand material

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  
<a name="module_helpers.specialLinks"></a>

### helpers.specialLinks
Resolve shebanq-specific links into working hyperlinks

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  
<a name="module_helpers.colorDefault"></a>

### helpers.colorDefault
Computes the default color

The data for the computation comes from the server
and is stored in the javascript global variables `Config`
`colorsDefault`, `nDefaultClrCols`, `nDefaultClrRows`.

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  
<a name="module_helpers.closeDialog"></a>

### helpers.closeDialog
Close a dialog box

**Kind**: static constant of [<code>helpers</code>](#module_helpers)  
<a name="module_helpers..mEscape"></a>

### helpers~mEscape()
Escape the `_` character in strings that must be rendered as markdown.

**Kind**: inner method of [<code>helpers</code>](#module_helpers)  
