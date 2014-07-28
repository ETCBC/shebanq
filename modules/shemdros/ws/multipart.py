#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright 2014 DANS-KNAW
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    ws_tests://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Classes for handling multi part http responses.
"""

import requests
import logging
from cStringIO import StringIO  # prior to python version 3
# from io import StringIO

class MultiPartDirector(object):
    """
    MultiPartDirector decides what ContentHandler shall handle the content of different bodyParts.
    The default behavior of this MultiPartDirector is to always return a standard ContentHandler.
    Implementers that wish to get control over what ContentHandler should handle which body part's content
    should subclass this class.
    """
    def handler_for(self, bodypart):
        """
        Get the handler for content of the given BodyPart. The given BodyPart instance should have parsed all header
        lines of the body part for which a contentHandler is requested.

        """
        return ContentHandler()


class ContentHandler(object):
    """
    Handler for the content lines in a multi part body part. This handler collects all lines of content in a StringIO.
    """
    def __init__(self):
        self.content = StringIO()

    def __handle_line__(self, line):
        print >>self.content, line  # prior to python version 3
        # print(line, file=self.content)

    def __end_content__(self):
        pass

    def content_as_string(self):
        """Return: collected content as string."""
        return self.content.getvalue()


class BodyPart(object):
    """
    A BodyPart can be fed with lines from a multi part response. Initially a BodyPart is in read_header mode:
    lines fed into handle_line(line) will not be added to the content but, if applicable, will be treated as
    header lines. As soon as a blank line ('') passes, all subsequent lines will be added to the content, unless
    the line starts with '--' + boundary, which signals the end of the body part.
    """
    def __init__(self, boundary, content_handler=None):
        """
        Initialize a BodyPart with the boundary in use for the multi part.
        If no content_handler is given a default handler will be used.
        """
        self.boundary = boundary
        self.read_header = True
        self.content_type = None
        self.start_content = None
        self.disposition = None
        self.filename = None
        if content_handler is None:
            self.content_handler = ContentHandler()
        else:
            self.content_handler = content_handler

    def set_content_handler(self, content_handler):
        """
        Set a ContentHandler for this BodyPart.

        Argument:
        - content_handler: a ContentHandler
        """
        assert isinstance(content_handler, ContentHandler)
        self.content_handler=content_handler

    def handle_line(self, line):
        """
        Handle lines from a multi part.

        Argument:
        - line: a line from a multi part.

        Return:
        True as long as subsequent lines are part of this body part, False otherwise.
        """
        self.start_content=False
        clean_line = line.strip()
        if not self.read_header:
            if clean_line.startswith("--" + self.boundary):
                self.content_handler.__end_content__()
                return False
            else:
                self.content_handler.__handle_line__(clean_line)
        elif self.read_header and clean_line.startswith("--" + self.boundary):
            pass
        elif self.read_header and clean_line=='':
            self.read_header=False
            self.start_content=True
        elif self.read_header:
            if clean_line.startswith("Content-Type:"):
                self.content_type = clean_line.split(":")[1].lstrip().rstrip()
            elif clean_line.startswith("Content-Disposition:"):
                values = clean_line.split(":")[1]
                split_values = values.split(";")
                self.disposition = split_values[0].lstrip()
                self.filename=split_values[1].split("=")[1].strip().lstrip('"').rstrip('"')
        return True

    def content_as_string(self):
        """Return: collected content as string."""
        return self.content_handler.content_as_string()


class MultiPart(object):
    """
    Class for handling multi part http responses.
    """
    def __init__(self, response, multi_part_director=None):
        """
        Initialize a MultiPart.

        Arguments:
        - response: a requests.Response

        Keyword arguments:
        - multi_part_director: a MultiPartDirector
        """
        assert isinstance(response, requests.Response)
        self.response = response
        self.boundary = None
        self.mime_type = None
        self.body_parts = []
        if multi_part_director is None:
            self.multi_part_director = MultiPartDirector()
        else:
            assert isinstance(multi_part_director, MultiPartDirector)
            self.multi_part_director = multi_part_director
        self.__handle_response__()


    def __handle_response__(self):
        if 'content-type' not in self.response.headers:
            raise Exception("No 'content-type' key in response.headers.")

        # multipart/mixed; boundary=Boundary_17_1928578963_1395926830776
        split_head = self.response.headers['content-type'].split(";")
        self.mime_type = split_head[0]
        split_boundary = split_head[1].split("=")
        self.boundary = split_boundary[1].strip()

        bph = BodyPart(self.boundary)
        self.body_parts.append(bph)
        for line in self.response.iter_lines():
            if line == "--" + self.boundary + "--":
                bph.handle_line(line)
                break
            if bph.handle_line(line):
                if bph.start_content:
                    bph.set_content_handler(self.multi_part_director.handler_for(bph))
            else:
                bph = BodyPart(self.boundary)
                self.body_parts.append(bph)

        logging.debug("Created multipart from " + self.response.url)