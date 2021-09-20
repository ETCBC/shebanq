#!/usr/bin/env python

from markdown import markdown
from helpers import hEsc, sanitize, isodt
from urls import Urls

from check import CHECK
from caching import CACHING
from query import QUERY

Check = CHECK(request)
Caching = CACHING(cache)
Query = QUERY(Check, Caching, auth, db, PASSAGE_DBS, VERSIONS)

U = Urls(URL)


def atom():
    session.forget(response)
    queries = Query.feed()
    icon = URL("static", "images/shebanq_logo_xxsmall.png", host=True)
    cover = URL("static", "images/shebanq_cover.png", host=True)
    base = URL("xxx", "yyy", host=True, extension="")[0:-8]
    feed = URL("feed", "atom", host=True, extension="")
    xml = []
    xml.append(
        """<?xml version="1.0" encoding="utf-8"?>
"""
    )
    xml.append(
        """
<feed
        xmlns="http://www.w3.org/2005/Atom"
        xmlns:webfeeds="http://webfeeds.org/rss/1.0"
>"""
    )
    xml.append(
        f"""
    <title>SHEBANQ</title>
    <subtitle>Shared queries, recently executed</subtitle>
    <link href="{hEsc(feed)}" rel="self"
        title="SHEBANQ - Shared Queries" type="application/atom+xml"/>
    <link href="{hEsc(base)}" rel="alternate" type="text/html"/>
    <id>{hEsc(base + "/hebrew/queries")}</id>
    <updated>{isodt()}</updated>
    <category term="bible study"/>
    <category term="biblical studies"/>
    <category term="text"/>
    <category term="linguistic"/>
    <category term="hebrew"/>
    <category term="bible"/>
    <category term="query"/>
    <category term="database"/>
    <category term="research"/>
    <category term="scholar"/>
    <category term="annotation"/>
    <category term="digital bible"/>
    <category term="digital"/>
    <category term="religion"/>
    <category term="theology"/>
    <icon>{hEsc(icon)}</icon>
    <webfeeds:icon>{hEsc(icon)}</webfeeds:icon>
    <logo>{hEsc(cover)}</logo>
    <webfeeds:cover image="{hEsc(cover)}"/>
    <webfeeds:accentColor>DDBB00</webfeeds:accentColor>
"""
    )

    for (queryId, ufname, ulname, qname, qdesc, qvid, qexe, qver) in queries:
        descHtml = U.specialLinks(
            sanitize(
                markdown(hEsc(qdesc or "No description given"), output_format="xhtml5")
            )
        )
        # we add a standard cover image if the description does not contain any image
        standardImage = (
            f"""<p><img src="{cover}"/></p>"""
            if """<img """ not in descHtml
            else ""
        )
        href = hEsc(
                    URL(
                        "hebrew",
                        "query",
                        vars=dict(id=queryId, version=qver),
                        host=True,
                        extension="",
                    )
                )
        tag = f"tag:shebanq.ancient-data.org,2016-01-01:{queryId}/{qvid}/{qver}"
        name = hEsc(f"{ufname} {ulname}")
        xml.append(
            f"""
    <entry>
        <title>{hEsc(qname)}</title>
        <link href="{href}" rel="alternate" type="text/html"/>
        <id>{tag}</id>
        <updated>{isodt(qexe)}</updated>
        <category term="query"/>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                {standardImage}
                {descHtml}
            </div>
        </content>
        <author><name>{name}</name></author>
    </entry>
"""
        )
    xml.append(
        """
</feed>
"""
    )
    return dict(xml="".join(xml))
