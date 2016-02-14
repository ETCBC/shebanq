#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from gluon.custom_import import track_changes; track_changes(True)
from markdown import markdown
from datetime import datetime
from render import h_esc, feed, special_links, sanitize, set_URL

def isodt(dt=None): return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") if dt==None else dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def atom():
    session.forget(response)
    queries = feed(db)
    set_URL(URL) # take care that in the module render.py the name URL is known
    icon_image = URL('static', 'images/shebanq_logo_small.png', host=True)
    icon_image_svg = URL('static', 'images/shebanq_logo.svg', host=True)
    logo_image = URL('static', 'images/shebanq_logo_medium.png', host=True)
    cover_image = URL('static', 'images/shebanq_cover.png', host=True)
    now = datetime.utcnow()
    self_base = URL('xxx', 'yyy', host=True, extension='')[0:-8]
    self_feed = URL('feed', 'atom', host=True, extension='')
    xml = []
    xml.append(u'''<?xml version="1.0" encoding="utf-8"?>
''')
    xml.append(u'''
<feed
        xmlns="http://www.w3.org/2005/Atom"
        xmlns:webfeeds="http://webfeeds.org/rss/1.0"
>''')
    xml.append(u'''
    <title>SHEBANQ</title>
    <subtitle>Shared queries, recently executed</subtitle>
    <link href="{}" rel="self" title="SHEBANQ - Shared Queries" type="application/atom+xml"/>
    <link href="{}" rel="alternate" type="text/html"/>
    <id>{}</id>
    <updated>{}</updated>
    <category term="hebrew"/>
    <category term="bible"/>
    <category term="database"/>
    <icon>{}</icon>
    <webfeeds:icon>{}</webfeeds:icon>
    <logo>{}</logo>
    <webfeeds:cover image="{}"/>
    <webfeeds:accentColor>DDBB00</webfeeds:accentColor>
'''.format(
    h_esc(self_feed),
    h_esc(self_base),
    h_esc(self_base+'/hebrew/queries'),
    isodt(),
    h_esc(icon_image),
    h_esc(icon_image_svg),
    h_esc(cover_image),
    h_esc(cover_image),
))

    for (qid, ufname, ulname, qname, qdesc, qvid, qexe, qver) in queries:
        desc_html = special_links(sanitize(markdown(h_esc(qdesc or 'No description given'), output_format='xhtml5')))
# we add a standard cover image if the description does not contain any image
        standard_image = u'''<p><img src="{}"/></p>'''.format(cover_image) if u'''<img ''' not in desc_html else u''
        xml.append(u'''
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
'''.format(
    h_esc(qname),
    h_esc(URL('hebrew', 'query', vars=dict(id=qid, version=qver), host=True, extension='')),
    'tag:{},{}:{}/{}/{}'.format('shebanq.ancient-data.org', '2016-01-01', qid, qvid, qver),
    isodt(qexe),
    standard_image,
    desc_html,
    h_esc(u'{} {}'.format(ufname, ulname)),
))
    xml.append(u'''
</feed>
''')
    return dict(xml=u''.join(xml))
