# -*- coding: utf-8 -*-
title = u'יֹּ֥אמֶר'
import unicodedata
x = unicodedata.normalize('NFKD', title).encode('ascii','ignore')
x = title.encode('ascii', 'backslashreplace')
print('[{}]'.format(x))
