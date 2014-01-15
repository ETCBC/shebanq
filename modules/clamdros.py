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

import clam.common.client
import clam.common.data
import clam.common.status
import random
import sys
import time
import props
import os.path

from lxml import etree

class Client(object):

    def __init__(self):
        self.project = "shebanq" + str(random.getrandbits(64))
        self.clamclient = clam.common.client.CLAMClient(props.clamdros_url)#, props.clamdros_username, props.clamdros_password)

    def query(self, input_filename, contexthandlername="level", contextlevel=0, contextmark='context'):
        self.clamclient.create(self.project)
        data = self.clamclient.get(self.project)
        self.clamclient.addinputfile(self.project, data.inputtemplate("mql-query"), input_filename)
        data = self.clamclient.startsafe(self.project,
                                         contexthandlername=contexthandlername,
                                         contextlevel=contextlevel,
                                         contextmark=contextmark)

        while data.status != clam.common.status.DONE:
            #print "not ready, going to sleep"
            time.sleep(1) #wait 1 seconds before polling status
            data = self.clamclient.get(self.project) #get status again
            print >>sys.stderr, "\tRunning: " + str(data.completion) + '% -- ' + data.statusmessage

        result_context =  self.render(data.output[0])
        return data.output, result_context

    def render(self, context_file):
        xslPath = os.path.dirname(__file__) + "/render.xsl"
        xslRoot = etree.fromstring(open(xslPath).read())
        transform = etree.XSLT(xslRoot)

        list = context_file.readlines()
        #for item in list:
        #    print item
        xmlRoot = etree.fromstringlist(list)
        #print ">>>>>>>>> xmlRoot <<<<<<<<<<<<"
        #print(etree.tostring(xmlRoot, pretty_print=True))
        #print ">>>>>>>>> xmlRoot <<<<<<<<<<<<"

        transRoot = transform(xmlRoot)
        return etree.tostring(transRoot)


    def remove(self):
        self.clamclient.delete(self.project)


