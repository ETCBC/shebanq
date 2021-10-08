<a name="module_colorpicker"></a>

## colorpicker

* [colorpicker](#module_colorpicker)
    * [.ColorPicker1](#module_colorpicker.ColorPicker1)
        * [new exports.ColorPicker1()](#new_module_colorpicker.ColorPicker1_new)
    * [.ColorPicker2](#module_colorpicker.ColorPicker2)
        * [new exports.ColorPicker2()](#new_module_colorpicker.ColorPicker2_new)

<a name="module_colorpicker.ColorPicker1"></a>

### colorpicker.ColorPicker1
**Kind**: static class of [<code>colorpicker</code>](#module_colorpicker)  
**See**

- [∈ highlight-select-single-color][elem-highlight-select-single-color]
- [∈ highlight-select-color][elem-highlight-select-color]

<a name="new_module_colorpicker.ColorPicker1_new"></a>

#### new exports.ColorPicker1()
the ColorPicker associated with individual items

These pickers show up in lists of items (in mq and mw sidebars) and
near individual items (in rq and rw sidebars).
They also have a checkbox, stating whether the color counts as customized.
Customized colors are held in a global colorMap,
which is saved in a cookie upon every picking action.

All actions are processed by the highlight2 (!) method
of the associated Settings object.

<a name="module_colorpicker.ColorPicker2"></a>

### colorpicker.ColorPicker2
**Kind**: static class of [<code>colorpicker</code>](#module_colorpicker)  
**See**: [∈ highlight-select-single-color][elem-highlight-select-single-color]  
<a name="new_module_colorpicker.ColorPicker2_new"></a>

#### new exports.ColorPicker2()
the ColorPicker associated with the view settings in a sidebar

These pickers show up at the top of the individual sidebars,
only on mq and mw sidebars.
They are used to control the uniform color with which
the results are to be painted.
They can be configured for dealing with background or foreground painting.
The paint actions depend on the mode of coloring
that the user has selected in settings.
So the paint logic is more involved.
But there is no associated checkbox.
The selected color is stored in the highlight settings,
which are synchronized in a cookie.
All actions are processed by the highlight2 method
of the associated Settings object.

