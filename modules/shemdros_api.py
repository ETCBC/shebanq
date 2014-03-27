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
from gluon.rewrite import params
from pip import exceptions

if 0:
    from . import *
    # End of fake imports to satisfy the editor.
    #

import requests
import props
import os
# long import statement for editor and web2py
from applications.shebanq.modules import multiPart
reload(multiPart)
from purl import URL
from lxml import etree

def result_to_html(xml_tree):
    xsl_path = os.path.dirname(__file__) + "/render2.xsl"
    xsl_tree = etree.parse(xsl_path)
    transform = etree.XSLT(xsl_tree)
    html_tree = transform(xml_tree)
    return html_tree

class ResponseException(Exception):

    def __init__(self, response, message=None):
        assert isinstance(response, requests.Response)
        msg = str(response.status_code) + '\n' + response.text
        if message is not None:
            msg = message + "\n" + msg
        Exception.__init__(self, msg)
        self.response = response


class RemoteException(ResponseException):
    pass


class ResponseParseException(ResponseException):
    pass


class Resource(object):

    def __init__(self):
        self.url=URL()\
            .scheme(props.shemdros_scheme)\
            .host(props.shemdros_host)\
            .port(props.shemdros_port)\
            .path(props.shemdros_root)

    def execute(self, url, stream=False):
        self.response = requests.get(str(url), stream=stream)
        return self.response

    @staticmethod
    def listResponse(response):
        assert isinstance(response, requests.Response)
        if response.status_code != 200:
            raise RemoteException(response)
        list = []
        for line in response.iter_lines():
            list.append(line)
        return list


class ShemdrosResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    def noPath(self):
        return self.execute(self.url)

    def getDatabases(self, stream=False):
        url = self.url.add_path_segment("databases")
        return self.execute(url, stream)

    def listDatabases(self):
        return Resource.listResponse(self.getDatabases(stream=True))

    def getJsonFiles(self, name=None, stream=False):
        url = self.url.add_path_segment("jsonfiles")
        if name is not None:
            url = url.add_path_segment(name)
        return self.execute(url, stream)

    def listJsonFiles(self):
        return Resource.listResponse(self.getJsonFiles(stream=True))

    def getEnvPools(self, stream=False):
        url = self.url.add_path_segment("envpools")
        return self.execute(url, stream)

    def listEnvPools(self):
        return Resource.listResponse(self.getEnvools(stream=True))


class MqlResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.url = self.url.add_path_segment("mql")

    def noPath(self):
        return self.execute(self.url)

    def getResultFormats(self, stream=False):
        url = self.url.add_path_segment("result-formats")
        return self.execute(url, stream)

    def listResultFormats(self):
        return Resource.listResponse(self.getResultFormats(stream=True))

    def getRenderers(self, stream=False):
        url = self.url.add_path_segment("renderers")
        return self.execute(url, stream)

    def listRenderers(self):
        return Resource.listResponse(self.getRenderers(stream=True))

    def query(self, query, database="default", result_format="mql-xml", stream=False):
        url = self.url.add_path_segment("query")
        params = {'database':database, 'result-format':result_format}
        response = requests.post(str(url), params=params, data=query, stream=stream)
        return response

    def render(self, query, database="default", json_name="default", renderer="level", context_level=0,\
               context_mark="context", offset_first=0, offset_last=0, stream=False):
        url = self.url.add_path_segment("render")
        params = {'database':database, 'json-name':json_name, 'renderer':renderer, 'context-level':context_level,\
                  'context-mark':context_mark, 'offset-firts':offset_first, 'offset-last':offset_last}
        response = requests.post(str(url), params=params, data=query, stream=stream)
        return response

    def queryAndRender(self, query, database="default", result_format="mql-xml", json_name="default",\
                    renderer="level", context_level=0, context_mark="context", offset_first=0, offset_last=0,\
                    stream=False):
        url = self.url.add_path_segment("execute")
        params = {'database':database, 'result-format':result_format, 'json-name':json_name, 'renderer':renderer, \
                  'context-level':context_level, 'context-mark':context_mark, 'offset-firts':offset_first, \
                  'offset-last':offset_last}
        response = requests.post(str(url), params=params, data=query, stream=stream)
        return response

    def getMqlXml(self, query, database="default"):
        response = self.query(query, database=database)
        if response.status_code != 200:
            raise RemoteException(response)
        return dict(mql_xml=response.text)


    def getContextHtml(self, query, database="default", json_name="default", renderer="level", context_level=0,\
               context_mark="context", offset_first=0, offset_last=0):
        response = self.render(query, database=database, json_name=json_name, renderer=renderer,\
                    context_level=context_level, context_mark=context_mark, offset_first=offset_first,\
                    offset_last=offset_last, stream=True)
        if response.status_code != 200:
            raise RemoteException(response)

        parser = etree.XMLParser()
        for line in response.iter_lines():
            parser.feed(line)
        xml_tree = parser.close()
        html_tree = result_to_html(xml_tree)

        return dict(context_html=etree.tostring(html_tree))

    def getMqlAndContextHtml(self, query, database="default", result_format="mql-xml", json_name="default",\
                    renderer="level", context_level=0, context_mark="context", offset_first=0, offset_last=0):
        response = self.queryAndRender(query, database=database, result_format=result_format, json_name=json_name,\
                    renderer=renderer, context_level=context_level, context_mark=context_mark, \
                    offset_first=offset_first, offset_last=offset_last, stream=True)

        if response.status_code != 200:
            raise RemoteException(response)

        director = MqlAndContextDirector()
        mp = multiPart.MultiPart(response, multipart_director=director)

        print (mp.mime_type)
        print (mp.boundery)
        for bp in mp.bodyparts:
            print(bp.content_type)
            print(bp.disposition)
            print(bp.filename)
            print(bp.getcontent_as_string())

        print(len(mp.bodyparts))


class MqlAndContextDirector(multiPart.MultiPartDirector):

    def getHandlerFor(self, bodypart):
        if "mql-context.xml" == bodypart.filename:
            return MqlContextHandler()
        else:
            return multiPart.ContentHandler()


class MqlContextHandler(multiPart.ContentHandler):

    def __init__(self):
        self.parser = etree.XMLParser()

    def __handleline__(self, line):
        self.parser.feed(line)

    def __end_content__(self):
        self.xml_tree = self.parser.close()
        self.html_tree = result_to_html(self.xml_tree)

    def getcontent_as_string(self):
        return etree.tostring(self.html_tree)



if __name__ == '__main__':
    import time
    sh = ShemdrosResource()

    # response = sh.noPath()
    # print(type(response))
    #
    # print(sh.getDatabases().text)
    #
    # print(sh.getJsonFiles().text)
    #
    # print(sh.getJsonFiles("default").status_code)
    #
    # print(sh.getJsonFiles("foo").headers)
    #
    # list = sh.listDatabases()
    # print(list)
    # for db in list:
    #     print(db)
    #
    # response = sh.getDatabases(stream=True)
    # for line in response.iter_lines():
    #     time.sleep(1)
    #     print(line)
    #
    mq = MqlResource()
    #
    # response = mq.noPath()
    # print(response.text)
    #
    # print(mq.getResultFormats().text)
    #
    # print(mq.listRenderers())
    #
    f = open('test-files/input/bh_lq01.mql', 'r')
    query = f.read()

    # response = mq.query(query, database='other')
    # print(response.headers)
    #
    # print(mq.render(query).text)
    #
    # d = mq.getMqlXml(query)
    # print(d)
    #
    d = mq.getContextHtml(query)
    print(d)

    #response = mq.queryAndRender(query)
    #print(response.headers['content-type'])
    #print(response.text)

    d = mq.getMqlAndContextHtml(query)
    print(d)

    # multipart/mixed; boundary=Boundary_3_429738776_1395677545737
    # --Boundary_3_429738776_1395677545737
    # Content-Type: text/xml
    #
    # --Boundary_3_429738776_1395677545737
    # Content-Type: text/xml
    #



