#!/usr/bin/env python

# from gluon.custom_import import track_changes; track_changes(True)
from markdown import markdown
from datetime import datetime
from helpers import h_esc, feed, sanitize
from urls.py import Urls


U = Urls(URL)


def isodt(dt=None):
    return (
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if dt is None
        else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def atom():
    session.forget(response)
    queries = feed(db)
    icon_image = URL("static", "images/shebanq_logo_xxsmall.png", host=True)
    cover_image = URL("static", "images/shebanq_cover.png", host=True)
    self_base = URL("xxx", "yyy", host=True, extension="")[0:-8]
    self_feed = URL("feed", "atom", host=True, extension="")
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
    <link href="{h_esc(self_feed)}" rel="self"
        title="SHEBANQ - Shared Queries" type="application/atom+xml"/>
    <link href="{h_esc(self_base)}" rel="alternate" type="text/html"/>
    <id>{h_esc(self_base + "/hebrew/queries")}</id>
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
    <icon>{h_esc(icon_image)}</icon>
    <webfeeds:icon>{h_esc(icon_image)}</webfeeds:icon>
    <logo>{h_esc(cover_image)}</logo>
    <webfeeds:cover image="{h_esc(cover_image)}"/>
    <webfeeds:accentColor>DDBB00</webfeeds:accentColor>
"""
    )

    for (qid, ufname, ulname, qname, qdesc, qvid, qexe, qver) in queries:
        desc_html = U.special_links(
            sanitize(
                markdown(h_esc(qdesc or "No description given"), output_format="xhtml5")
            )
        )
        # we add a standard cover image if the description does not contain any image
        standard_image = (
            f"""<p><img src="{cover_image}"/></p>"""
            if """<img """ not in desc_html
            else ""
        )
        href = h_esc(
                    URL(
                        "hebrew",
                        "query",
                        vars=dict(id=qid, version=qver),
                        host=True,
                        extension="",
                    )
                )
        tag = f"tag:shebanq.ancient-data.org,2016-01-01:{qid}/{qvid}/{qver}"
        name = h_esc(f"{ufname} {ulname}")
        xml.append(
            f"""
    <entry>
        <title>{h_esc(qname)}</title>
        <link href="{href}" rel="alternate" type="text/html"/>
        <id>{tag}</id>
        <updated>{isodt(qexe)}</updated>
        <category term="query"/>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                {standard_image}
                {desc_html}
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
