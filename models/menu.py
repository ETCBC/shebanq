#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 DANS-KNAW
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# #######################################################################
# Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
if 0:
    from . import *
# End of fake imports to satisfy the editor.
# #######################################################################

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################


response.logo = A(IMG(_src=URL('static', 'images/shebanq_logo_small.png')),
                  _class="brand",
                  _href="http://arxiv.org/abs/1501.01866",
                  _target="_blank",
                  _style="margin-bottom: -2em;",
                  )


served_on = request.env.SERVER_NAME
on_system = False
on_local = False
on_prod = False
on_devel = False
if served_on == None: on_system = True
elif served_on.endswith('local'): on_local = True
elif served_on == 'shebanq.ancient-data.org': on_prod = True
else: on_devel = True

#response.title = request.application.replace('_',' ').title()
response.title = request.function.replace('_', ' ').capitalize()
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'SHEBANQ <shebanq@ancient-data.org>'
response.meta.description = 'Search engine for biblical Hebrew based on ETCBC database (formerly known as WIVU)'
response.meta.keywords = 'Hebrew, Text Database, Bible, Query, Annotation'
response.meta.generator = 'ETCBC4 Data'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    ('' if on_prod else served_on, False, None, []),
    ('SHEBANQ', False, URL('default', 'index'), []),
    (T('The Text'), False, URL('hebrew', 'text', vars=dict(mr='m')), []),
    (T('Words'), False, URL('hebrew', 'words'), []),
    (T('Queries'), False, URL('hebrew', 'queries'), []),
    (T('Notes'), False, URL('hebrew', 'notes'), []),
    (T('Tools'), False, URL('tools', 'index'), []),
    (T('Help'), False, None, [
        (T('SHEBANQ user manual'), False, URL('default', 'help'), []),
        (T('SHEBANQ tutorial by Oliver'), False, URL('static', 'docs/Glanz_shebanq_tut.pdf'), []),
        (T('ETCBC feature doc'), False, URL('static', 'docs/featuredoc/features/comments/0_overview.html'), []),
        (T('ETCBC methods'), False, URL('methods', 'index'), []),
        (T('MQL quick reference guide (pdf)'), False, URL('static', 'docs/MQL-QuickRef.pdf'), []),
        (T('MQL Query Guide by Ulrik (pdf)'), False, URL('static', 'docs/MQL-Query-Guide.pdf'), []),
        (T('ETCBC4 transcription table (pdf)'), False, URL('static', 'docs/ETCBC4-transcription.pdf'), []),
        (T('REST API (for integrators)'), False, URL('default', 'restapi'), []),
    ]),
    (T('News'), False, URL('default', 'news'), []),
    (T('Sources'), False, URL('default', 'sources'), []),
]

if "auth" in locals(): auth.wikimenu() 
