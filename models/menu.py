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

#response.title = request.application.replace('_',' ').title()
response.title = request.function.replace('_', ' ').capitalize()
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Dirk Roorda <dirk.roorda@dans.knaw.nl>'
response.meta.description = 'Search engine for biblical Hebrew based on ETCBC database (formerly known as WIVU)'
response.meta.keywords = 'Hebrew, Text Database, Bible, Query, Annotation'
response.meta.generator = 'ETCBC4 Data'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Home'), False, URL('default', 'index'), []),
    (T('The Text'), False, URL('hebrew', 'text', vars=dict(mr='m')), []),
    (T('Words'), False, URL('hebrew', 'words'), []),
    (T('Queries'), False, URL('hebrew', 'queries'), []),
    (T('Help'), False, URL('default', 'help'), []),
    (T('News'), False, URL('default', 'news'), []),
    (T('Sources'), False, URL('default', 'sources'), []),
]

if "auth" in locals(): auth.wikimenu() 
