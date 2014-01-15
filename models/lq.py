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

from gluon.validators import Validator, is_empty


class IS_FILLED_OR_DEFAULT(Validator):
    """
    Replaces empty value with given default_value, otherwise returns value.
        >> IS_FILLED_OR_DEFAULT(0)('5')
        (5, None)

        >> IS_FILLED_OR_DEFAULT(0)('')
        (0, None)

        >> IS_FILLED_OR_DEFAULT('some value')('any')
        ('any', None)

        >> IS_FILLED_OR_DEFAULT('some value')('')
        ('some value', None)

    """
    def __init__(self, default_value, empty_regex=None):
        self.default_value = default_value
        if empty_regex is not None:
            self.empty_regex = re.compile(empty_regex)
        else:
            self.empty_regex = None

    def __call__(self, value):
        value, empty = is_empty(value, empty_regex=self.empty_regex)
        if empty:
            value = self.default_value
        return (value, None)

# Define the table that contains the handler types for query results
#db.define_table("mql_context_handler",
#    Field('name'),format='%(name)s')
# a = db.mql_context_handler.insert(name='level')
# b = db.mql_context_handler.insert(name='marks')
# print 'inserted ' + str(a) + ' ' + str(b)

# Define read-only signature
signature = db.Table(db,'auth_signature',
    Field('is_active','boolean',default=True,
          writable=False,readable=False),
    Field('created_on','datetime',default=request.now,
        writable=False,readable=True),
    Field('created_by',auth.settings.table_user,default=auth.user_id,
        writable=False,readable=True),
    Field('modified_on','datetime',update=request.now,default=request.now,
        writable=False,readable=True),
    Field('modified_by',auth.settings.table_user,
        default=auth.user_id,update=auth.user_id,
        writable=False,readable=True))

# Define the query table
db.define_table("mql_queries",
    Field('mql', 'text', requires=IS_NOT_EMPTY(error_message="Enter a query")),
    Field('handler_name', 'string',
          #requires=IS_IN_SET(range(2),('level', 'marks')), # field type: integer, default=0 | 1
          requires=IS_IN_SET({'level' : 'Level', 'marks' : 'Marks'}),
          default='level',
          widget=lambda k,v: SQLFORM.widgets.radio.widget(k, v, style='divs',),
        ),
    Field('context_level', 'integer', requires=[IS_FILLED_OR_DEFAULT(0), IS_INT_IN_RANGE(0)], default=0),
    Field('context_marker', 'string', requires=[IS_FILLED_OR_DEFAULT('context'), IS_NOT_EMPTY()], default='context'),
    signature)


