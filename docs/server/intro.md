# Server

This is the part of SHEBANQ that works on the server.

It consists of *controllers* that are triggered by urls.
The actual work of the controllers is implemented in the modules.

The result of that work is data, in the form of dictionaries.

These dictionaries are fed into views, which are chunks of HTML
with placeholders that are filled by the key value pairs in
the dictionary.
