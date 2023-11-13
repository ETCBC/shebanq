<a name="module_material"></a>

## material

* [material](#module_material)
    * [.Material](#module_material.Material)
        * [`.fetch()`](#module_material.Material+fetch)
        * [`.addVerseRefs()`](#module_material.Material+addVerseRefs)

<a name="module_material.Material"></a>

### material.Material
Controls the main area of the page.

**Kind**: static class of [<code>material</code>](#module_material)  
**See**

- [M:MATERIAL][materials.MATERIAL]
- page elements:
*    [∈ book][elem-book],
*    [∈ chapter][elem-chapter],
*    [∈ page][elem-page],
*    [∈ goto-chapter][elem-goto-chapter],


* [.Material](#module_material.Material)
    * [`.fetch()`](#module_material.Material+fetch)
    * [`.addVerseRefs()`](#module_material.Material+addVerseRefs)

<a name="module_material.Material+fetch"></a>

#### material.fetch()
get the material by AJAX if needed, and process the material afterwards

**Kind**: instance method of [<code>Material</code>](#module_material.Material)  
**See**: Triggers [C:hebrew.material][controllers.hebrew.material]  
<a name="module_material.Material+addVerseRefs"></a>

#### material.addVerseRefs()
add a click event to the verse number by which
linguistic features for the words in that verse
can be retrieved from the server.

**Kind**: instance method of [<code>Material</code>](#module_material.Material)  
**See**

- Triggers [C:hebrew.verse][controllers.hebrew.verse].
- [∈ show-verse-data][elem-show-verse-data]

