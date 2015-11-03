
# coding: utf-8

# <a href="http://laf-fabric.readthedocs.org/en/latest/" target="_blank"><img align="left" src="images/laf-fabric-xsmall.png"/></a>
# <a href="http://www.godgeleerdheid.vu.nl/etcbc" target="_blank"><img align="left" src="images/VU-ETCBC-xsmall.png"/></a>
# <a href="http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71" target="_blank"><img align="left"src="images/etcbc4easy-small.png"/></a>
# <a href="http://tla.mpi.nl" target="_blank"><img align="right" src="images/TLA-xsmall.png"/></a>
# <a href="http://www.dans.knaw.nl" target="_blank"><img align="right"src="images/DANS-xsmall.png"/></a>

# # Paragraphs from the px files

# In[1]:

import re
import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.extra import ExtraData
fabric = LafFabric()


# ## Create annotations from px file

# In[2]:

source = 'etcbc'
if 'version' not in locals(): version = '4b'


# In[ ]:

API=fabric.load(source+version, '--', 'shebanq', {
    "xmlids": {"node": True, "edge": False},
    "features": ('''
        otype monads number label
    ''',
    '''
    '''),
    "prepare": prepare,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))


# # Method to read px data

# In[ ]:

def read_px(px_file):
    msg("Making mappings between clause atoms in PX and nodes in LAF")
    ca_labn2id = {}
    ca_id2labn = {}
    for n in NN():
        otype = F.otype.v(n)
        if otype == 'verse':
            cur_label = F.label.v(n)
        elif otype == 'chapter':
            cur_subtract += cur_chapter_cas
            cur_chapter_cas = 0
        elif otype == 'book':
            cur_subtract = 0
            cur_chapter_cas = 0
        elif otype == 'clause_atom':
            cur_chapter_cas += 1
            nm = int(F.number.v(n)) - cur_subtract
            ca_labn2id[(cur_label, nm)] = n
            ca_id2labn[n] = (cur_label, nm)
    msg("End making mappings: {}={} clauses".format(len(ca_labn2id), len(ca_id2labn)))

    data = []
    not_found = set()
    px_handle = open(px_file)
    ln = 0
    can = 0
    featurescan = re.compile(r'0 0 (..) [0-9]+ LineNr\s*([0-9]+).*?Pargr:\s*([0-9.]+)')
    cur_label = None
    data = []
    for line in px_handle:
        ln += 1
        if line.strip()[0] != '*':
            cur_label = line[0:10]
            continue
        can += 1
        features = featurescan.findall(line)
        if len(features) == 0:
            msg("Warning: line {}: no instruction, LineNr, Pargr found".format(ln))
        elif len(features) > 1:
            msg("Warning: line {}: multiple instruction, LineNr, Pargr found".format(ln))
        else:
            feature = features[0]
            the_ins = feature[0]
            the_n = feature[1]
            the_para = feature[2]
            labn = (cur_label, int(the_n))
            if labn not in ca_labn2id:
                not_found.add(labn)
                continue
            data.append((ca_labn2id[labn], the_ins, the_n, the_para))
    px_handle.close()
    msg("Read {} paragraph annotations".format(len(data)))
    if not_found:
        msg("Could not find {} label/line entries in index: {}".format(len(not_found), sorted({lab for lab in not_found})))
    else:
        msg("All label/line entries found in index")
    return data


# # Integrating the px data
# 
# 

# In[ ]:

px = ExtraData(API)
px.deliver_annots(
    'para', 
    {'title': 'Paragraph numbers', 'date': '2015'},
    [
        ('px/px_data.{}'.format(source+version), 'px', read_px, (
            ('etcbc4', 'px', 'instruction'),
            ('etcbc4', 'px', 'number_in_ch'),
            ('etcbc4', 'px', 'pargr'),
        )),
    ],
)


# ## Checking: loading the new features

# In[4]:

API=fabric.load(source+version, 'para', 'shebanq', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        oid otype number label
        instruction number_in_ch pargr
    ''',
    '''
    '''),
    "prepare": prepare,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))


# # Generating MQL
# 
# We generate an text file with the new feature data which we will insert
# properly in the existing MQL dump of the ETCBC database.
# 
# The text file is structured as follows:
# 
# It consists of tab delimited lines, with a header line:
# 
#     object_type feature_name1 feature_name2 ...
# 
# followed by lines with the same number of fields.
# The first field is the object id, the subsequent fields are the values of the corresponding features for that object.

# In[5]:

pm = outfile('pargr_data.mql')
pm.write('{}\t{}\n'.format('clause_atom', 'pargr'))
chunk = 10000
nc = 0
ic = 0
for c in F.otype.s('clause_atom'):
    nc += 1
    ic += 1
    if ic == chunk: 
        ic = 0
        print('{:>5} clause atoms'.format(nc))
    pm.write('{}\t{}\n'.format(F.oid.v(c), F.pargr.v(c) or ''))
print('{:>5} clause atoms'.format(nc))
pm.close()


# ## Inspecting all objects that got new features

# In[6]:

pfile = 'paras.txt'
ph = outfile(pfile)
cur_label = None
for n in NN():
    otype = F.otype.v(n)
    if otype == 'verse':
        cur_label = F.label.v(n)
    elif otype == 'clause_atom':
        nm = F.number_in_ch.v(n)
        if nm:
            ph.write("{}: instruction = {}; {}; para = {}\n".format(cur_label, nm, F.instruction.v(n), F.pargr.v(n)))
ph.close()

i = 0
inf = infile(pfile)
for line in inf:
    i += 1
    if i > 26: break
    print(line.rstrip('\n'))
inf.close()
    
msg("Done")


# In[ ]:



