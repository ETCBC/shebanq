#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections, json, datetime

from gluon.custom_import import track_changes; track_changes(True)

EXPIRE = 3600*24*30

def index():
    session.forget(response)
    response.title = T("Tools")
    response.subtitle = T("Tools for the ETCBC4 database")
    return dict()

