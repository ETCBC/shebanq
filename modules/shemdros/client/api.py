#!/usr/bin/env python
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

"""
A Python version of the API for the shemdros web service.
"""

import os
from lxml import etree # prior to python version 3
from purl import URL
from ConfigParser import SafeConfigParser
from shemdros.ws.multipart import *


def result_to_html(xml_tree, xsl_file=os.path.dirname(__file__) + "/stylesheets/render2.xsl"):
    xsl_tree = etree.parse(xsl_file)
    transform = etree.XSLT(xsl_tree)
    html_tree = transform(xml_tree)
    return html_tree


def sanitize(query):
    lines = query.splitlines()
    slines = []
    for line in lines:
        slines.append(line.split('//', 1)[0])
    slines.append('GO')
    return '\n'.join(line.replace('\/', '/') for line in slines)
        

class ClientException(Exception):
    pass


class ResponseException(Exception):

    def __init__(self, response, message=None):
        assert isinstance(response, requests.Response)
        msg = 'status_code: ' + str(response.status_code) + '\nremote_message:\n' + response.text
        if message is not None:
            msg = 'client_tests message: ' + message + "\n" + msg
        Exception.__init__(self, msg)
        self.response = response


class RemoteException(ResponseException):
    pass


class ResponseParseException(ResponseException):
    pass


class Configuration():

    def __init__(self):
        parser = SafeConfigParser()
        logging.debug("Trying to find the configuration file for shemdros.client.api")
        c_path = ['/usr/local/shemdros/shemdros.cfg', 'shemdros.cfg']
        logging.debug("Trying these locations: " + str(c_path))
        for path in c_path:
            if not os.path.isabs(path):
                path = os.path.dirname(__file__) + "/" + path
            if os.path.isfile(path):
                print("Found configuration file: " + path)
                break
        if not os.path.isfile(path):
            logging.error("No configuration file found in locations " + str(c_path))
            raise Exception("No configuration file found in locations " + str(c_path))

        logging.info("Trying to configure shemdros.client.api with configuration found at " + path)
        try:
            parser.read(path)
            self.server_scheme = parser.get('server', 'scheme')
            self.server_host = parser.get('server', 'host')
            self.server_port = parser.getint('server', 'port')
            self.server_root = parser.get('server', 'root')
        except:
            logging.error("A correct configuration file is expected at " + path)

config = Configuration()


class Resource(object):

    def __init__(self):
        self.url = URL()\
            .scheme(config.server_scheme)\
            .host(config.server_host)\
            .port(config.server_port)\
            .path(config.server_root)
        self.response = None

    def execute(self, url=None, stream=False, timeout=None):
        if url is None:
            url = self.url
        self.response = requests.get(str(url), stream=stream, timeout=timeout)
        return self.response

    def list_response(self, response=None):
        if response is None:
            if self.response is None:
                raise ClientException('No response available.')
            response = self.response
        assert isinstance(response, requests.Response)
        if response.status_code != 200:
            raise RemoteException(response)
        response_list = []
        for line in response.iter_lines():
            response_list.append(line)
        return response_list


class MonadSetHandler():

    def set_monad_set(self, first, last):
        pass


class ShemdrosResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    def no_path(self):
        return self.execute(self.url)

    def application_wadl(self, detail=False, stream=False):
        url = self.url.add_path_segment("application.wadl")
        if detail:
            url = url.append_query_param('detail', 'true')
        return self.execute(url, stream)

    def version(self):
        url = self.url.add_path_segment("version")
        return self.execute(url, False)

    def databases(self, stream=False):
        url = self.url.add_path_segment("databases")
        return self.execute(url, stream)

    def jsonfiles(self, name=None, stream=False):
        url = self.url.add_path_segment("jsonfiles")
        if name is not None:
            url = url.add_path_segment(name)
        return self.execute(url, stream)

    def envpools(self, stream=False):
        url = self.url.add_path_segment("envpools")
        return self.execute(url, stream)


class MqlResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.url = self.url.add_path_segment("mql")

    def no_path(self):
        return self.execute()

    def result_formats(self, stream=False):
        url = self.url.add_path_segment("result-formats")
        return self.execute(url, stream)

    def renderers(self, stream=False):
        url = self.url.add_path_segment("renderers")
        return self.execute(url, stream)

    def query(self, query, database="default", result_format="mql-xml", stream=False):
        url = self.url.add_path_segment("query")
        params = {'database':database, 'result-format':result_format}
        self.response = requests.post(str(url), params=params, data=sanitize(query), stream=stream)
        return self.response

    # The render methods cannot be used because elements in the xml-output of Emdros are mismatched.
    # def render(self, query, database="default", json_name="default", renderer="level", context_level=0,\
    #            context_mark="context", offset_first=0, offset_last=0, stream=False):
    #     url = self.url.add_path_segment("render")
    #     params = {'database':database, 'json-name':json_name, 'renderer':renderer, 'context-level':context_level,\
    #               'context-mark':context_mark, 'offset-first':offset_first, 'offset-last':offset_last}
    #     self.response = requests.post(str(url), params=params, data=query, stream=stream)
    #     return self.response

    def query_and_render(self, query, database="default", result_format="mql-xml", json_name="default",\
                    renderer="level", context_level=0, context_mark="context", offset_first=0, offset_last=0,\
                    stream=False):
        url = self.url.add_path_segment("execute")
        params = {'database':database, 'result-format':result_format, 'json-name':json_name, 'renderer':renderer, \
                  'context-level':context_level, 'context-mark':context_mark, 'offset-first':offset_first, \
                  'offset-last':offset_last}
        self.response = requests.post(str(url), params=params, data=sanitize(query), stream=stream)
        return self.response

    def get_mql_xml(self, query, database="default"):
        response = self.query(query, database=database)
        if response.status_code != 200:
            raise RemoteException(response)
        return dict(mql_xml=response.text)


    # The render methods cannot be used because elements in the xml-output of Emdros are mismatched.
    # def get_context_html(self, query, database="default", json_name="default", renderer="level", context_level=0,\
    #            context_mark="context", offset_first=0, offset_last=0):
    #     response = self.render(query, database=database, json_name=json_name, renderer=renderer,\
    #                 context_level=context_level, context_mark=context_mark, offset_first=offset_first,\
    #                 offset_last=offset_last, stream=True)
    #     if response.status_code != 200:
    #         raise RemoteException(response)
    #
    #     parser = etree.XMLParser()
    #     for line in response.iter_lines():
    #         parser.feed(line)
    #
    #     xml_tree = parser.close()
    #     html_tree = result_to_html(xml_tree)
    #     html = etree.tostring(html_tree)
    #     return dict(context_html=html)

    def get_mql_and_context_html(self, query, database="default", result_format="mql-xml", json_name="default",\
                    renderer="level", context_level=0, context_mark="context", offset_first=0, offset_last=0):
        response = self.query_and_render(query, database=database, result_format=result_format, json_name=json_name,\
                    renderer=renderer, context_level=context_level, context_mark=context_mark, \
                    offset_first=offset_first, offset_last=offset_last, stream=True)

        if response.status_code != 200:
            raise RemoteException(response)

        mp = MultiPart(response, multi_part_director=MqlAndContextDirector())

        multi = dict()
        for bp in mp.body_parts:
            multi[bp.filename]=bp.content_as_string()

        return multi

    def get_monad_set_csv(self, query, database="default", stream=False):
        url = self.url.add_path_segment("query")
        params = {'database':database, 'result-format':"monadset-csv"}
        self.response = requests.post(str(url), params=params, data=sanitize(query), stream=stream)

        if self.response.status_code != 200:
            raise RemoteException(self.response)

        return self.response

    def get_monad_set_xml(self, query, database="default", stream=False):
        url = self.url.add_path_segment("query")
        params = {'database':database, 'result-format':"monadset-xml"}
        self.response = requests.post(str(url), params=params, data=sanitize(query), stream=stream)

        if self.response.status_code != 200:
            raise RemoteException(self.response)

        return self.response

    def list_monad_set(self, query, database="default"):
        """

        :param query: the mql query to execute
        :param database: the name of the database
        :return: a list of monadsets, each set contains two monads, first and last.
        """
        self.get_monad_set_csv(query, database=database, stream=True)

        list = []
        for line in self.response.iter_lines():
            fl = line.split(';')
            list.append([int(fl[0]), int(fl[1])])
        return list

    def handle_query(self, query, handler=MonadSetHandler(), database="default"):
        self.get_monad_set_csv(query, database=database, stream=True)
        #print(self.response.iter_lines().next())
        for line in self.response.iter_lines():
            fl = line.split(';')
            print([int(fl[0]), int(fl[1])])
            handler.set_monad_set(int(fl[0]), int(fl[1]))


class MonadsetIterator():

    def __init__(self, query, database="default"):
        self.response = MqlResource().get_monad_set_csv(query, database=database, stream=True)
        self.monadsets_iter = self.response.iter_lines()

    def __iter__(self):
        return self

    def next(self):
        fl = self.monadsets_iter.next().split(';')
        return [int(fl[0]), int(fl[1])]


class CashedMonadsetIterator(MonadsetIterator):

    def __init__(self, query, database="default"):
        self.monadsets = []
        self.response = MqlResource().get_monad_set_csv(query, database=database, stream=True)
        for line in self.response.iter_lines():
            fl = line.split(';')
            self.monadsets.append([int(fl[0]), int(fl[1])])

        self.monadsets_iter = self.monadsets.__iter__()

    def next(self):
        return self.monadsets_iter.next()


class MqlAndContextDirector(MultiPartDirector):

    def handler_for(self, bodypart):
        if "mql-context.xml" == bodypart.filename:
            bodypart.filename = "mql-context.html"
            return MqlContextHandler()
        else:
            return ContentHandler()


class MqlContextHandler(ContentHandler):

    def __init__(self):
        self.parser = etree.XMLParser()
        self.xml_tree = None
        self.html_tree = etree.fromstring('<div/>')

    def __handle_line__(self, line):
        self.parser.feed(line)

    def __end_content__(self):
        self.xml_tree = self.parser.close()
        self.html_tree = result_to_html(self.xml_tree)

    def content_as_string(self):
        return etree.tostring(self.html_tree)
