# Technical Home

What it is, how it is designed, how it works and how it can be installed and maintained.

## About

SHEBANQ is a website built as an application in the
[Web2py]({{web2py}}) framework.
It uses [MySQL]({{mysql}}) databases to store its dynamic data,
which is generated by users, and its static data, which consists
of the text of the hebrew Bible and linguistic annotations
of the [ETCBC]({{etcbc}}).

The static data is delivered via the [BHSA]({{bhsa}}) repository,
where it arrived through a [pipeline]({{pipeline}})) from
the source data as it sits on ETCBC servers.

The speciality of SHEBANQ is that it offers users the facility to
run queries against the data and to store those queries so that they
can be shared and published.

The query engine for this is [Emdros]({{emdros}}) which sits on top
of MySQL and speaks with it.

Shebanq and the pipeline have been constructed using
[Text-Fabric]({{textfabric}}) as the main tool.

There are several kinds of documentation of SHEBANQ,
see [documentation](deploy/documentation.md) where it is described
how to maintain that information.

In order to develop effectively, we use a test framework,
see [testing](tests/index.md).

Quickly jump to a topic below,
or use the navigation controls.

## Conventions

### Code references


This documentation contains many references to all kind of things.

Some references have shapes that help you recognize to what they refer:

*   `[∈ element]` refers to a page element called *element*; it links
    to its documentation;
*   `[M:XXX.yyy]` refers to Python code for `yyy` in module `modules/xxx.py`;
*   `[C:xxx.yyy]` refers to Python controller `yyy()` in file `controllers/xx;x.py`
*   `[{xxx.yyy}]` refers to Javascript code for `yyy` in file `static/js/app/x;xx.js`

## Topics

*   [Elements of the page](elements/index.md)
*   Installation on
    [personal computers](deploy/computer.md) and
    [servers](deploy/server.md)
*   [Maintenance](deploy/maintenance.md)
*   [Testing](tests/index.md)
