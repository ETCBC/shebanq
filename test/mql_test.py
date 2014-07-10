# !/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright 2014 DANS-KNAW
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

import unittest

from controllers.mql import *


class Test_mql(unittest.TestCase):

    def setUp(self):
        self.env = new_env(app='init', controller='default')
        self.db = copy_db(self.env, db_name='db', db_link='sqlite:memory')

    def test_parse_exception(self):
        error_xml = "bla"
        result = parse_exception(error_xml)
        print result
