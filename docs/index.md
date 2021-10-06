# SHEBANQ Technical documentation

What it is, how it is designed, how it works and how it can be installed and maintained.

## About

SHEBANQ is a website built as an application in the
[Web2Py]({{web2py}}) framework.
It uses [MySQL]({{mysql}}) databases to store its dynamic data,
which is generated by users, and its static data, which consists
of the text of the hebrew Bible and linguistic annotations
of the [ETCBC]({{etcbc}}).

The static data is delivered via the [BHSA]({{bhsa}}) repository,
where it arrived through a [pipeline]({{pipeline}})) from
the source data as it sits on ETCBC servers.

The specialty of SHEBANQ is that it offers users the facility to
run queries against the data and to store those queries so theat they
can be shared and published.

The query engine for this is [Emdros]({{emdros}}) which sits on top
of MySQL and speaks with it.

Shebanq and the pipeline have been constructed using
[Text-Fabric]({{textfabric}}) as the main tool.

Quickly jump to a topic below,
or use the navigation controls.

## Topics

*   [Elements of the page](topics/elements.md)
*   Installation on
    [personal computers](deploy/computer.md) and
    [servers](deploy/server.md)
*   [Maintenance](deploy/maintenance.md)