<a name="module_sidecontent"></a>

## sidecontent

* [sidecontent](#module_sidecontent)
    * [.SideContent](#module_sidecontent.SideContent)
        * [.sendVal()](#module_sidecontent.SideContent+sendVal)
        * [.sendVals()](#module_sidecontent.SideContent+sendVals)
        * [.fetch()](#module_sidecontent.SideContent+fetch)

<a name="module_sidecontent.SideContent"></a>

### sidecontent.SideContent
Controls the content of a side bar

**Kind**: static class of [<code>sidecontent</code>](#module_sidecontent)  

* [.SideContent](#module_sidecontent.SideContent)
    * [.sendVal()](#module_sidecontent.SideContent+sendVal)
    * [.sendVals()](#module_sidecontent.SideContent+sendVals)
    * [.fetch()](#module_sidecontent.SideContent+fetch)

<a name="module_sidecontent.SideContent+sendVal"></a>

#### sideContent.sendVal()
Updates a single field of a query.

Meant for `is_shared` and `is_published`.

!!! note
    `is_shared` is a field of a query record.

    `is_published` is a field of a `query_exe` record.

**Kind**: instance method of [<code>SideContent</code>](#module_sidecontent.SideContent)  
**See**: Triggers [C:hebrew.querysharing][controllers.hebrew.querysharing].  
<a name="module_sidecontent.SideContent+sendVals"></a>

#### sideContent.sendVals()
Sends un updated record to the database.

**Kind**: instance method of [<code>SideContent</code>](#module_sidecontent.SideContent)  
**See**: Triggers [C:hebrew.queryupdate][controllers.hebrew.queryupdate].  
<a name="module_sidecontent.SideContent+fetch"></a>

#### sideContent.fetch()
get the material by AJAX if needed, and process the material afterwards

This method takes into account what kind of sidebar this is:

**Kind**: instance method of [<code>SideContent</code>](#module_sidecontent.SideContent)  
**See**

- Triggers [C:hebrew.sidematerial][controllers.hebrew.sidematerial]
- Triggers [C:hebrew.sideword][controllers.hebrew.sideword]
- Triggers [C:hebrew.sidequery][controllers.hebrew.sidequery]
- Triggers [C:hebrew.sidenote][controllers.hebrew.sidenote]

