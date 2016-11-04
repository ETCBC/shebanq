#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections, json, datetime

from gluon.custom_import import track_changes; track_changes(True)

EXPIRE = 3600*24*30

def index():
    session.forget(response)
    response.title = T("Methods")
    response.subtitle = T("ETCBC methods")
    return dict()

def references():
    session.forget(response)
    response.title = T("References")
    response.subtitle = T("Extensive list of ETCBC related papers")
    return dict()

