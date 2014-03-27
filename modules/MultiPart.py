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

import requests
from cStringIO import StringIO

class MultiPartDirector(object):

    def getHandlerFor(self, bodypart):
        # default behavior is to return a default ContentHandler
        return ContentHandler()


class ContentHandler(object):

    def __init__(self):
        self.content = StringIO()

    def __handleline__(self, line):
        print >>self.content, line

    def __end_content__(self):
        pass

    def getcontent_as_string(self):
        return self.content.getvalue()


class BodyPart(object):

    def __init__(self, boundery, content_handler=None):
        self.boundery = boundery
        self.read_header=True
        if content_handler is None:
            self.content_handler = ContentHandler()
        else:
            self.content_handler = content_handler

    def set_content_handler(self, content_handler):
        self.content_handler=content_handler

    def handleLine(self, line):
        self.start_content=False
        if not self.read_header:
            if line.startswith("--" + self.boundery):
                self.content_handler.__end_content__()
                return False
            else:
                self.content_handler.__handleline__(line)
        elif self.read_header and line.startswith("--" + self.boundery):
            pass
        elif self.read_header and line=='':
            self.read_header=False
            self.start_content=True
        elif self.read_header:
            if line.startswith("Content-Type:"):
                self.content_type = line.split(":")[1].lstrip()
            elif line.startswith("Content-Disposition:"):
                values = line.split(":")[1]
                splitvalues = values.split(";")
                self.disposition = splitvalues[0].lstrip()
                self.filename=splitvalues[1].split("=")[1].lstrip('"').rstrip('"')
        return True

    def getcontent_as_string(self):
        return self.content_handler.getcontent_as_string()


class MultiPart(object):

    def __init__(self, response, multipart_director=None):
        assert isinstance(response, requests.Response)
        self.response = response
        if multipart_director is None:
            self.multipart_director = MultiPartDirector()
        else:
            self.multipart_director = multipart_director
        self.__handle_response__()


    def __handle_response__(self):
        if 'content-type' not in self.response.headers:
            raise Exception("No 'content-type' key in response.headers.")

        # multipart/mixed; boundary=Boundary_17_1928578963_1395926830776
        splithead = self.response.headers['content-type'].split(";")
        self.mime_type = splithead[0]
        splitboundery = splithead[1].split("=")
        self.boundery = splitboundery[1]

        self.bodyparts=[]
        bph = BodyPart(self.boundery)
        self.bodyparts.append(bph)
        for line in self.response.iter_lines():
            if line=="--" + self.boundery + "--":
                bph.handleLine(line)
                break
            if bph.handleLine(line):
                if bph.start_content:
                    bph.set_content_handler(self.multipart_director.getHandlerFor(bph))
            else:
                bph = BodyPart(self.boundery)
                self.bodyparts.append(bph)








