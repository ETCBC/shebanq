# Javascript organization

The interaction with SHEBANQ is taken care of by a modern
Javascript app.

SHEBANQ uses vanilla Javascript (ES6 and higher), without any 
code pre-processing. The Javascript source is directly
included by the HTML.

We only use a few Javascript libraries:

*   [fancytree]({{fancytree}})
    for the overview pages of notes and queries;
*   [jQuery]({{jquery}})
    almost everywhere.

Most of the code is organized in modules under
*static/js/app*.

The modules are [individually documented](bymodule/index.md) 
by jsdocstrings in the code.

## Entry point

The entry point is `main.js`.
It has the following responsibilities:

*   Pick up a bunch of settings from the server
*   Set up `LocalStorage` in the browser to remember those settings
*   Make the settings available in an `ViewState` object that is globally accessible
*   Construct a Page object
*   Start the dynamics of the Page object

## Objects in general

Most of the objects defined in the javascript app share a general
way of working:

### Constructor

Object constructors do simple work, and do not depend on the outcomes
of asynchronous actions of other objects.
So it is always safe to construct an object.

### Initialization

If objects need initialization that depends on asynchronous work of
other objects, it should be put in an `init()` method.
These can be triggered by the `process()` methods of other objects.

### Fetch

If objects need to interact with the server, they use AJAX
to send/fetch data. When the response from the server has come back,
a callback is executed in which the method `process()` is called.

### Process

Everything that needs to be done with data that has been fetched
from the server, is done in this method.

Things to do are typically:

*   generate HTML out of JSON
*   dress up the DOM with events

### Apply

Whenever the `ViewState` changes, objects maybe affected.
Objects do not listen to the state themselves.
Whichever object changes the state must trigger the `apply()`
method of affected objects.


