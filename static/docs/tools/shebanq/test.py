
# coding: utf-8

# In[1]:

import sys
import collections

from laf.fabric import LafFabric
from etcbc.lib import Transcription
from etcbc.preprocess import prepare

fabric = LafFabric()


# In[2]:

source = 'etcbc'
version = '4b'
API = fabric.load(source+version, 'lexicon', 'shebanq', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype book
    ''',''),
    'primary': False,
    'prepare': prepare,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))


# In[3]:

for b in F.otype.s('book'):
    print(F.book.v(b))


# In[ ]:



