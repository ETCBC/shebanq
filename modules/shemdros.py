#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
A Python version of the API for the shemdros web service.
"""

import os
from lxml import etree # prior to python version 3
from purl import URL
from ConfigParser import SafeConfigParser
#from shemdros.ws.multipart import *
import logging, requests

class RemoteException(Exception):

    def __init__(self, response, message=None):
        assert isinstance(response, requests.Response)
        msg = 'status_code: ' + str(response.status_code) + '\nremote_message:\n' + response.text
        if message is not None:
            msg = 'client_tests message: ' + message + "\n" + msg
        Exception.__init__(self, msg)
        self.response = response


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


class MqlResource():

    def __init__(self):
        self.url = URL()\
            .scheme(config.server_scheme)\
            .host(config.server_host)\
            .port(config.server_port)\
            .path(config.server_root)
        self.response = None
        self.url = self.url.add_path_segment("mql")

    def _sanitize(self, query):
        lines = query.splitlines()
        slines = []
        for line in lines:
            slines.append(line.split('//', 1)[0])
        slines.append('GO')
        return '\n'.join(line.replace('\/', '/') for line in slines)
        
    def _get_monad_set_csv(self, query, database="default", stream=False):
        url = self.url.add_path_segment("query")
        params = {'database':database, 'result-format':"monadset-csv"}
        self.response = requests.post(str(url), params=params, data=self._sanitize(query), stream=stream)

        if self.response.status_code != 200:
            raise RemoteException(self.response)

        return self.response

    def list_monad_set(self, query, database="default"):
        """

        :param query: the mql query to execute
        :param database: the name of the database
        :return: a list of monadsets, each set contains two monads, first and last.
        """
        self._get_monad_set_csv(query, database=database, stream=True)

        list = []
        for line in self.response.iter_lines():
            fl = line.split(';')
            list.append([int(fl[0]), int(fl[1])])
        return list

