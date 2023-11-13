<a name="module_select"></a>

## select

* [select](#module_select)
    * `static`
        * [.SelectPassage](#module_select.SelectPassage)
            * [.apply()](#module_select.SelectPassage+apply)
            * [.selectVersion()](#module_select.SelectPassage+selectVersion)
        * [.SelectResultPage](#module_select.SelectResultPage)
        * [.SelectLanguage](#module_select.SelectLanguage)
    * `inner`
        * [~SelectBook](#module_select..SelectBook)
        * [~SelectItems](#module_select..SelectItems)

<a name="module_select.SelectPassage"></a>

### select.SelectPassage
Handles book and chapter selection

**Kind**: static class of [<code>select</code>](#module_select)  

* [.SelectPassage](#module_select.SelectPassage)
    * [.apply()](#module_select.SelectPassage+apply)
    * [.selectVersion()](#module_select.SelectPassage+selectVersion)

<a name="module_select.SelectPassage+apply"></a>

#### selectPassage.apply()
apply current passage selection

New material is fetched from the current data version;

The link to the feature documentation is adapted the
data version.

!!! caution
    But currently the docs are no longer
    dependent on the data version.

The links to other applications are adapted to the
new passage selection:

*   `bol` = [Bible Online Learner]({{bol}})
*   `pbl` = [ParaBible]({{parabible}})

**Kind**: instance method of [<code>SelectPassage</code>](#module_select.SelectPassage)  
**See**: Page elements:

*   [∈ info][elem-info]
*   [∈ version][elem-version]
*   [∈ links][elem-links]  
<a name="module_select.SelectPassage+selectVersion"></a>

#### selectPassage.selectVersion()
Switch to another version of the ETCBC data, such as 4b or 2021

*   [∈ version][elem-version]

**Kind**: instance method of [<code>SelectPassage</code>](#module_select.SelectPassage)  
<a name="module_select.SelectResultPage"></a>

### select.SelectResultPage
Handles selection of a result page

**Kind**: static class of [<code>select</code>](#module_select)  
<a name="module_select.SelectLanguage"></a>

### select.SelectLanguage
Handles selection of the language in which the names
of bible books are presented.

**Kind**: static class of [<code>select</code>](#module_select)  
**See**

- [M:`blang`][blang].
- [∈ language][elem-language].

<a name="module_select..SelectBook"></a>

### select~SelectBook
Handles book selection

**Kind**: inner class of [<code>select</code>](#module_select)  
**See**: [∈ book][elem-book]  
<a name="module_select..SelectItems"></a>

### select~SelectItems
Handles selection of chapters and result pages.

**Kind**: inner class of [<code>select</code>](#module_select)  
**See**: [∈ chapter][elem-chapter], [∈ page][elem-page]  
