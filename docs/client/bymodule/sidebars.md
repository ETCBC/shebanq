<a name="module_sidebars"></a>

## sidebars

* [sidebars](#module_sidebars)
    * `static`
        * [.Sidebars](#module_sidebars.Sidebars)
    * `inner`
        * [~Sidebar](#module_sidebars..Sidebar)

<a name="module_sidebars.Sidebars"></a>

### sidebars.Sidebars
Handles the sidebars.

Any kind is handled.
But it only manages the administration of whether content has been fetched
for the sidebar.
All things that depend on the kind of sidebar are delegated
to the [{sidebar}][sidebarssidebar] object.

**Kind**: static class of [<code>sidebars</code>](#module_sidebars)  
<a name="module_sidebars..Sidebar"></a>

### sidebars~Sidebar
Handles specific sidebars.

The `mr` and `qw` types are frozen into the object

**Kind**: inner class of [<code>sidebars</code>](#module_sidebars)  
