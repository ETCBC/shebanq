#!/usr/bin/env python
#-*- coding:utf-8 -*-

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

# # Fake imports and web2py variables. See also: __init__.py
# This code only serves to satisfy the editor. It is never executed.
if 0:
    from . import *
    # End of fake imports to satisfy the editor.
    #

@auth.requires_login()
def query():
    mql_record = db(db.mql_queries.created_by==auth.user).select().last() or 0

    mql_form = SQLFORM(db.mql_queries, record=mql_record,
        showid = False, ignore_rw=False,
        labels = {'mql':'mql query', 'handler_name':'Context '},
        col3 = {
            'mql':A('MQL Query Guide (pdf)',
                _target='_blank',
                _href='http://emdros.org/MQL-Query-Guide.pdf'),
            #'handler_name':'In what context should the result be presented'
        },
        formstyle='divs',
        buttons=[TAG.button('Save', _type='submit', _name='button_save'),
                TAG.button('Execute', _type='submit', _name='button_execute'),]
    )

    if mql_form.process(keepvalues=True).accepted:
        if request.vars.has_key('button_save'):
            response.flash = 'saved query'
        elif request.vars.has_key('button_execute'):
            response.flash = 'executing query'
    elif mql_form.errors:
        response.flash = 'form has errors, see details'

    return dict(form=mql_form)

