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

def lexiconlist():
    lli = request.vars.ll_include
    llx = request.vars.ll_exclude
    lexemes = dict(i=lli, x=llx)
    good = True
    return dict(data=json.dumps(dict(lexemes=lexemes, good=good)))

