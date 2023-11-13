# Server

This is the part of SHEBANQ that works on the server.

It consists of [controllers](controllers.md) that are triggered by urls.
The actual work of the controllers is implemented in the
[modules](bymodule/index.md).

The result of that work is data, in the form of dictionaries.

These dictionaries are fed into
[views](views.md), which are chunks of HTML with placeholders
that are filled by the key value pairs in the dictionary.

For every controller function like

```
def xxx():
    produce a dictionary
```

there is a view with the same name: *xxx.html*,
in which the result of `xxx()` will be filled in.

!!! note "Not strict"
    There might be more functions in a controller file than are
    controllers: auxiliary functions are allowed.

    There might be more HTML files in the views directory
    than are proper views: views may include sub views.
