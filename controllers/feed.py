#!/usr/bin/env python

# from gluon.custom_import import track_changes; track_changes(True)
from markdown import markdown
from datetime import datetime
from render import h_esc, feed, special_links, sanitize, set_URL


def isodt(dt=None):
    return (
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if dt is None
        else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def atom():
    session.forget(response)
    queries = feed(db)
    set_URL(URL)  # take care that in the module render.py the name URL is known
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
        """
    <title>SHEBANQ</title>
    <subtitle>Shared queries, recently executed</subtitle>
    <link href="{}" rel="self"
        title="SHEBANQ - Shared Queries" type="application/atom+xml"/>
    <link href="{}" rel="alternate" type="text/html"/>
    <id>{}</id>
    <updated>{}</updated>
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
    <icon>{}</icon>
    <webfeeds:icon>{}</webfeeds:icon>
    <logo>{}</logo>
    <webfeeds:cover image="{}"/>
    <webfeeds:accentColor>DDBB00</webfeeds:accentColor>
""".format(
            h_esc(self_feed),
            h_esc(self_base),
            h_esc(self_base + "/hebrew/queries"),
            isodt(),
            h_esc(icon_image),
            h_esc(icon_image),
            h_esc(cover_image),
            h_esc(cover_image),
        )
    )

    for (qid, ufname, ulname, qname, qdesc, qvid, qexe, qver) in queries:
        desc_html = special_links(
            sanitize(
                markdown(h_esc(qdesc or "No description given"), output_format="xhtml5")
            )
        )
        # we add a standard cover image if the description does not contain any image
        standard_image = (
            """<p><img src="{}"/></p>""".format(cover_image)
            if """<img """ not in desc_html
            else ""
        )
        xml.append(
            """
    <entry>
        <title>{}</title>
        <link href="{}" rel="alternate" type="text/html"/>
        <id>{}</id>
        <updated>{}</updated>
        <category term="query"/>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                {}
                {}
            </div>
        </content>
        <author><name>{}</name></author>
    </entry>
""".format(
                h_esc(qname),
                h_esc(
                    URL(
                        "hebrew",
                        "query",
                        vars=dict(id=qid, version=qver),
                        host=True,
                        extension="",
                    )
                ),
                "tag:{},{}:{}/{}/{}".format(
                    "shebanq.ancient-data.org", "2016-01-01", qid, qvid, qver
                ),
                isodt(qexe),
                standard_image,
                desc_html,
                h_esc("{} {}".format(ufname, ulname)),
            )
        )
    xml.append(
        """
</feed>
"""
    )
    return dict(xml="".join(xml))
