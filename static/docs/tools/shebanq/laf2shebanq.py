
# coding: utf-8

# <a href="http://laf-fabric.readthedocs.org/en/latest/" target="_blank"><img align="left" src="images/laf-fabric-xsmall.png"/></a>
# <a href="http://emdros.org" target="_blank"><img align="left" src="files/images/Emdros-xsmall.png"/></a>
# <a href="http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71" target="_blank"><img align="left"src="images/etcbc4easy-small.png"/></a>
# <a href="http://www.godgeleerdheid.vu.nl/etcbc" target="_blank"><img align="right" src="images/VU-ETCBC-xsmall.png"/></a>
# <a href="http://tla.mpi.nl" target="_blank"><img align="right" src="images/TLA-xsmall.png"/></a>
# <a href="http://www.dans.knaw.nl" target="_blank"><img align="right"src="images/DANS-xsmall.png"/></a>

# # LAF2SHEBANQ

# This notebook constructs a relational database, *passage*, meant to support browsing of texts and highlighting of words.
# It contains the texts themselves, verse by verse, and it contains book and chapter information.
# The *passage* database also contains a lexicon, which is linked to the word occurrences.
# 
# See the MySQL create statements below.

# In[1]:

import sys
import collections

from laf.fabric import LafFabric
from etcbc.lib import Transcription
from etcbc.preprocess import prepare

fabric = LafFabric()


# In[ ]:

source = 'etcbc'
if 'version' not in locals(): version = '4b'


# In[2]:

API = fabric.load(source+version, 'lexicon', 'shebanq', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        oid otype monads minmonad maxmonad
        book chapter verse
        g_cons g_cons_utf8 g_word g_word_utf8 trailer_utf8
        g_qere_utf8 qtrailer_utf8
        language lex g_lex lex_utf8 sp pdp ls
        vt vs gn nu ps st
        nme pfm prs uvf vbe vbs
        g_entry g_entry_heb gloss
        phono phono_sep
        function typ rela txt det
        code tab
        number
    ''',''),
    'prepare': prepare,
}, verbose='NORMAL')
exec(fabric.localnames.format(var='fabric'))


# # Data model
# 
# The data model of the browsing database as as follows:
# 
# There are tables ``book``, ``chapter``, ``verse``, ``word_verse``, ``lexicon``, ``clause_atom``.
# 
# The tables ``book``, ``chapter``, ``verse``, ``clause_atom`` contain fields ``first_m``, ``last_m``, 
# denoting the first and last monad number of that book, chapter, verse, clause_atom.
# 
# A ``book``-record contains an identifier and the name of the book.
# 
# A ``chapter``-record contains an identifier, the number of the chapter, and a foreign key to the record in the ``book`` table to which the chapter belongs.
# 
# A ``verse``-record contains an identifier, the number of the verse, and a foreign key to the record in the ``chapter`` table to which the verse belongs. More over, it contains the text of the whole verse in two formats:
# 
# In field ``text``: the plain unicode text string of the complete verse.
# 
# In field ``xml``: a sequence of ``<w>`` elements, one for each word in the verse, containing the plain unicode text string of that word as element content.
# The monad number of that word is stored in an attribute value. 
# The monad number is a globally unique sequence number of a word occurrence in the Hebrew Bible, going from 1 to precisely 426,555.
# There is also a lexical identifier stored in an attribute value.
# The lexical identifier points to the lexical entry that corresponds with the word.
# 
#     <w m="2" l="3">רֵאשִׁ֖ית </w>
# 
# As you see, the material between a word and the next word is appended to the first word. So, when you concatenate words, whitespace or other separators are needed.
# 
# A ``word_verse``-record links a word to a verse. 
# The monad number is in field ``anchor``, which is an integer, 
# and the verse is specified in the field ``verse_id`` as foreign key.
# The field ``lexicon_id`` is a foreign key into the ``lexicon`` table.
# 
# There is also a ``word`` table, meant to store all the information to generate a rich representation of the hebrew text,
# its syntactic structure, and some linguistic properties.
# See that notebook for a description and an example of the rich hebrew text representation.
# 
# The rich data is added per word, but the data has a dependency on the verses the words are contained in.
# In general, information about sentences, clauses and phrases will be displayed on the first words of those objects,
# but if the object started in a previous verse, this information is repeated on the first word of that object in the
# current verse.
# This insures that the display of a verse is always self-contained.
# 
# The ``word`` table has no field ``id``, its primary key is the field called ``word_number``. 
# This fields contains the same monad number as is used in the field ``anchor`` of the table ``word_verse``.
# 
# A ``clause_atom`` record contains an identifier, and the book to which it belongs, and its sequence number within 
# that book.
# In SHEBANQ, manual annotations are linked to the clause atom, so we need this information to easily fetch comments to
# passages and to compose charts and csv files.
# 
# ## Lexicon
# 
# A ``lexicon`` record contains the various lexical fields, such as identifiers, entry representations,
# additional lexical properties, and a gloss.
# 
# We make sure that we translate lexical feature values into values used for the etcbc4.
# We need the following information per entry:
# 
# * **id** a fresh id (see below), to be used in applications, unique over **entryid** and **lan**
# * **lan** the language of the entry, in ISO 639-3 abbreviation
# * **entryid** the string used as entry in the lexicon and as value of the ``lex`` feature in the text
# * **g_entryid** the Hebrew untransliteration of entryid, with the disambiguation marks unchanged, corresponds to the ``lex_utf8`` feature
# * **entry** the unpointed transliteration (= **entryid** without disambiguation marks)
# * **entry_heb** the unpointed hebrew representation, obtained by untransliterating **entry**
# * **g_entry** the pointed transliteration, without disambiguation marks, obtained from ``vc``
# * **g_entry_heb** the pointed hebrew representation, obtained by untransliterating **g_entry**
# * **root** the root, obtained from ``rt``
# * **pos** the part of speech, obtained from ``sp``
# * **nametype** the type of named entity, obtained from ``sm``
# * **subpos** subtype of part of speech, obtained from ``ls`` (aka *lexical set*)
# * **gloss** the gloss from ``gl``
# 
# We construct the **id** from the ``lex`` feature as follows:
# 
# * allocate a varchar(32)
# * the > is an alef, we translate it to A
# * the < is an ayin, we translate it to O
# * the / denotes a noun, we translate it to n
# * the [ denotes a verb, we translate it to v
# * the = is for disambiguation, we translate it to i
# * we prepend a language identifier, 1 for Hebrew, 2 for aramaic.
# 
# This is sound, see the scheck in the extradata/lexicon notebook

# # Field transformation
# 
# The lexical fields require a bit of attention.
# The specification in ``lex_fields`` below specifies the lexicon fields in the intended order.
# It contains instructions how to construct the field values from the lexical information obtained from the lexicon files.
# 
#     (source, method, name, transformation table, data type, data size, data options, params)
# 
# ## source 
# May contain one of the following:
# 
# * the name of a lexical feature as shown in the lexicon files, such as ``sp``, ``vc``.
# * None. 
#   In this case, **method** is a code that triggers special actions, such as getting an id or something that is available to the   program that fills the lexicon table
# * the name of an other field as shown in the **name** part of the specification. 
#   In this case, **method** is a function, defined else where, that takes the value of that other field as argument. 
#   The function is typically a transliteration, or a stripping action.
# 
# ## method
# May contain one of the following:
# 
# * a code (string), indicating:
#     * ``lex``: take the value of a feature (indicated in **source**) for this entry from the lexicon file
#     * ``entry``: take the value of the entry itself as found in the lexicon file
#     * ``id``: take the id for this entry as generated by the program
#     * ``lan``: take the language of this entry
# * a function taking one argument
#     * *strip_id*: strip the non-lexeme characters at the end of the entry (the ``/ [ =`` characters)
#     * *to_heb*: transform the transliteration into real unicode Hebrew
#     * feature lookup functions such as ``F.lex.v``
# 
# ## name
# The name of the field in the to be constructed table ``lexicon`` in the database ``passage``.
# 
# ## data type
# The sql data type, such as ``int`` or ``varchar``, without the size and options.
# 
# ## data size
# The sql data size, which shows up between ``()`` after the data type
# 
# ## data options
# Any remaining type specification, such as `` character set utf8``.
# 
# ## params
# Params consists currently of 1 boolean, indicating whether the field is defined on all words of the object, or only on its first word.

# # Index of ketiv/qere
# 
# We make a list of the ketiv-qere items.
# It will be used by the *heb* and the *ktv* functions.
# 
# *heb()* provides the surface text of a word.
# When the qere is different from the ketiv, the vocalized qere is chosen.
# It is the value of ``g_word_utf8`` except when a qere is present, 
# in which case it is ``g_qere_utf8``, preceded by a masora circle.
# This is the sign for the user to use data view to inspect the *ketiv*.
# 
# *ktv()* provides the surface text of a word, in case the ketiv is different from the qere.
# It is the value of ``g_word_utf8`` precisely when a qere is present, 
# otherwise it is empty.

# In[3]:

qeres = {}
masora = '֯'
msg('Building qere index')
for w in F.g_qere_utf8.s():
    qeres[w] = (masora+F.g_qere_utf8.v(w), F.qtrailer_utf8.v(w))
msg('Found {} qeres'.format(len(qeres)))


# ## Field types

# In[4]:

def strip_id(entryid):
    return entryid.rstrip('/[=')

def to_heb(translit):
    return Transcription.to_hebrew(Transcription.suffix_and_finales(translit)[0])

def heb(n):
    if n in qeres:
        (trsep, wrdrep) = qeres[n]
    else:
        trsep = F.trailer_utf8.v(n)
        wrdrep = F.g_word_utf8.v(n)
    if trsep.endswith('ס') or trsep.endswith('פ'): trsep += ' '
    return wrdrep + trsep

def ktv(n):
    if n in qeres:
        trsep = F.trailer_utf8.v(n)
        if trsep.endswith('ס') or trsep.endswith('פ'): trsep += ' '
        return F.g_word_utf8.v(n) + trsep    
    return ''

def lang(n):
    return 'hbo' if F.language.v(n) == 'Hebrew' else 'arc'

def df(f):
    def g(n): 
        val = f(n)
#        if val == None or val == "None" or val == "none" or val == "NA" or val == "N/A" or val == "n/a":
        if val == None:
            return '#null'
        return val
    return g

lex_fields = (
    (None, 'id', 'id', None, 'varchar', 32, ' primary key'),
    (None, 'lan', 'lan', None, 'char', 4, ''),
    (None, 'entry', 'entryid', None, 'varchar', 32, ''),
    ('entryid', strip_id, 'entry', None, 'varchar', 32, ''),
    ('entry', to_heb, 'entry_heb', None, 'varchar', 32, ' character set utf8'),
    ('entryid', to_heb, 'entryid_heb', None, 'varchar', 32, ' character set utf8'),
    ('vc', 'lex', 'g_entry', None, 'varchar', 32, ''),
    ('g_entry', to_heb, 'g_entry_heb', None, 'varchar', 32, ' character set utf8'),
    ('rt', 'lex', 'root', None, 'varchar', 32, ''),
    ('sp', 'lex', 'pos', None, 'varchar', 8, ''),
    ('sm', 'lex', 'nametype', None, 'varchar', 16, ''),
    ('ls', 'lex', 'subpos', None, 'varchar', 8, ''),
    ('gl', 'lex', 'gloss', None, 'varchar', 32, ' character set utf8'),
)
word_fields = (
    (F.monads.v, 'number', 'word', 'int', 4, ' primary key', False),
    (heb, 'heb', 'word', 'varchar', 32, '', False),
    (ktv, 'ktv', 'word', 'varchar', 32, '', False),
    (F.g_entry_heb.v, 'vlex', 'word', 'varchar', 32, '', False),
    (F.lex_utf8.v, 'clex', 'word', 'varchar', 32, '', False),
    (F.g_word.v, 'tran', 'word', 'varchar', 32, '', False),
    (F.phono.v, 'phono', 'word', 'varchar', 32, '', False),
    (F.phono_sep.v, 'phono_sep', 'word', 'varchar', 8, '', False),
    (F.lex.v, 'lex', 'word', 'varchar', 32, '', False),
    (F.g_lex.v, 'glex', 'word', 'varchar', 32, '', False),
    (F.gloss.v, 'gloss', 'word', 'varchar', 32, '', False),
    (lang, 'lang', 'word', 'varchar', 8, '', False),
    (df(F.sp.v), 'pos', 'word', 'varchar', 8, '', False),
    (df(F.pdp.v), 'pdp', 'word', 'varchar', 8, '', False),
    (df(F.ls.v), 'subpos', 'word', 'varchar', 8, '', False),
    (df(F.vt.v), 'tense', 'word', 'varchar', 8, '', False),
    (df(F.vs.v), 'stem', 'word', 'varchar', 8, '', False),
    (df(F.gn.v), 'gender', 'word', 'varchar', 8, '', False),
    (df(F.nu.v), 'gnumber', 'word', 'varchar', 8, '', False),
    (df(F.ps.v), 'person', 'word', 'varchar', 8, '', False),
    (df(F.st.v), 'state', 'word', 'varchar', 8, '', False),
    (df(F.nme.v), 'nme', 'word', 'varchar', 8, '', False),
    (df(F.pfm.v), 'pfm', 'word', 'varchar', 8, '', False),
    (df(F.prs.v), 'prs', 'word', 'varchar', 8, '', False),
    (df(F.uvf.v), 'uvf', 'word', 'varchar', 8, '', False),
    (df(F.vbe.v), 'vbe', 'word', 'varchar', 8, '', False),
    (df(F.vbs.v), 'vbs', 'word', 'varchar', 8, '', False),
    (None, 'border', 'subphrase', 'varchar', 16, '', False),
    ('id', 'number', 'subphrase', 'varchar', 32, '', False),
    (df(F.rela.v), 'rela', 'subphrase', 'varchar', 8, '', True),
    (None, 'border', 'phrase', 'varchar', 8, '', False),
    (F.number.v, 'number', 'phrase_atom', 'int', 4, '', False),
    (df(F.rela.v), 'rela', 'phrase_atom', 'varchar', 8, '', True),
    (F.number.v, 'number', 'phrase', 'int', 4, '', False),
    (df(F.function.v), 'function', 'phrase', 'varchar', 8, '', True),
    (df(F.rela.v), 'rela', 'phrase', 'varchar', 8, '', True),
    (df(F.typ.v), 'typ', 'phrase', 'varchar', 8, '', True),
    (df(F.det.v), 'det', 'phrase', 'varchar', 8, '', True),
    (None, 'border', 'clause', 'varchar', 8, '', False),
    (F.number.v, 'number', 'clause_atom', 'int', 4, '', False),
    (df(F.code.v), 'code', 'clause_atom', 'varchar', 8, '', True),
    (df(F.tab.v), 'tab', 'clause_atom', 'int', 4, '', False),
    (F.number.v, 'number', 'clause', 'int', 4, '', False),
    (df(F.rela.v), 'rela', 'clause', 'varchar', 8, '', True),
    (df(F.typ.v), 'typ', 'clause', 'varchar', 8, '', True),
    (df(F.txt.v), 'txt', 'clause', 'varchar', 8, '', False),
    (None, 'border', 'sentence', 'varchar', 8, '', False),
    (F.number.v, 'number', 'sentence_atom', 'int', 4, '', False),
    (F.number.v, 'number', 'sentence', 'int', 4, '', False),
)
first_only = dict(('{}_{}'.format(f[2], f[1]), f[6]) for f in word_fields)


# # Sanity
# The texts and xml representations of verses are stored in ``varchar`` fields.
# We have to make sure that the values fit within the declared sizes of these fields.
# The code measures the maximum lengths of these fields, and it turns out that the text is maximally 434 chars and the xml 2186 chars.

# In[5]:

field_limits = {
    'book': {
        'name': 32,
    },
    'verse': {
        'text': 1024,
        'xml': 4096,
    },
    'clause_atom': {
        'text': 512,
    },
    'lexicon': {},
}
for f in lex_fields:
    if f[4].endswith('char'):
        field_limits['lexicon'][f[2]] = f[5]

config = {
    'db': 'shebanq_passage'+version,
}
for tb in field_limits:
    for fl in field_limits[tb]: config['{}_{}'.format(tb, fl)] = field_limits[tb][fl]

text_create_sql = '''
drop database if exists {db};

create database {db} character set utf8;

use {db};

create table book(
    id      int(4) primary key,
    first_m int(4),
    last_m int(4),
    name varchar({book_name}),
    index(name)
);

create table chapter(
    id int(4) primary key,
    first_m int(4),
    last_m int(4),
    book_id int(4),
    chapter_num int(4),
    foreign key (book_id) references book(id),
    index(chapter_num)
);

create table verse(
    id int(4) primary key,
    first_m int(4),
    last_m int(4),
    chapter_id int(4),
    verse_num int(4),
    text varchar({verse_text}) character set utf8,
    xml varchar({verse_xml}) character set utf8,
    foreign key (chapter_id) references chapter(id)
);

create table clause_atom(
    id int(4) primary key,
    first_m int(4),
    last_m int(4),
    ca_num int(4),    
    book_id int(4),
    text varchar({clause_atom_text}) character set utf8,
    foreign key (book_id) references book(id),
    index(ca_num)
);

create table word(
    {{wordfields}}
);

create table lexicon(
    {{lexfields}}    
) collate utf8_bin;

create table word_verse(
    anchor int(4) unique,
    verse_id int(4),
    lexicon_id varchar(32),
    foreign key (anchor) references word(word_number),
    foreign key (verse_id) references verse(id),
    foreign key (lexicon_id) references lexicon(id)
) collate utf8_bin;

'''.format(**config).format(
        lexfields = ',\n    '.join('{} {}({}){}'.format(
            f[2], f[4], f[5], f[6],
        ) for f in lex_fields),
        wordfields = ', \n    '.join('{}_{} {}({}){}'.format(
            f[2], f[1], f[3], f[4], f[5],
    ) for f in word_fields),
)
print(text_create_sql)


# # Lexicon file reading

# In[6]:

langs = {'hbo', 'arc'}
lex_base = dict((lan, '{}/{}/{}.{}{}'.format(API['data_dir'], 'lexicon', lan, source, version)) for lan in langs)
lang_map = {
    'Hebrew': 'hbo',
    'Aramaic': 'arc',
}

def read_lex(lan):
    lex_infile = open(lex_base[lan], encoding='utf-8')

    lex_items = {}
    ln = 0
    e = 0
    for line in lex_infile:
        ln += 1
        line = line.split('#')[0]
        line = line.rstrip()
        if line == '': continue
        (entry, featurestr) = line.split(sep=None, maxsplit=1)
        entry = entry.strip('"')
        if entry in lex_items:
            sys.stderr.write('duplicate lexical entry {} in line {}.\n'.format(entry, ln))
            e += 1
            continue
        if featurestr.startswith(':') and featurestr.endswith(':'):
            featurestr = featurestr.strip(':')
        featurestr = featurestr.replace('\\:', chr(254))
        featurelst = featurestr.split(':')
        features = {}
        for feature in featurelst:
            comps = feature.split('=', maxsplit=1)
            if len(comps) == 1:
                if feature.strip().isnumeric():
                    comps = ('_n', feature.strip())
                else:
                    sys.stderr.write('feature without value for lexical entry {} in line {}: {}\n'.format(entry, ln, feature))
                    e += 1
                    continue
            (key, value) = comps
            value = value.replace(chr(254), ':')
            if key in features:
                sys.stderr.write('duplicate feature for lexical entry {} in line {}: {}={}\n'.format(entry, ln, key, value))
                e += 1
                continue
            features[key] = value
        if 'sp' in features and features['sp'] == 'verb':
            if 'gl' in features:
                gloss = features['gl']
                if gloss.startswith('to '):
                    features['gl'] = gloss[3:]
        lex_items[entry] = features
        
    lex_infile.close()
    msgstr = "Lexicon {}: there w".format(lan) + ('ere {} errors'.format(e) if e != 1 else 'as 1 error') + '\n'
    sys.stderr.write(msgstr)
    return lex_items

lex_entries = dict((lan, read_lex(lan)) for lan in sorted(langs))
for lan in sorted(lex_entries):
    print('Lexicon {} has {:>5} entries'.format(lan, len(lex_entries[lan])))


# ## Lexicon result
# The result is also stored in a tab separated file, which can be downloaded from my
# [SURFdrive](https://surfdrive.surf.nl/files/public.php?service=files&t=f910f1e088d1dfc9fc526e408ab07c45).

# # Table filling
# 
# We compose all the records for all the tables.
# 
# We also generate a file that can act as the basis of an extra annotation file with lexical information.

# In[7]:

msg("Fill the tables ... ")
cur_id = {
    'book': -1,
    'chapter': - 1,
    'verse': -1,
    'clause_atom': -1
}

def s_esc(sql): return sql.replace("'", "''").replace('\\','\\\\').replace('\n','\\n')

cur_verse_node = None
cur_verse_info = []
cur_verse_first_m = None
cur_verse_last_m = None
cur_lex_values = {}

lex_index = {}
lex_not_found = collections.defaultdict(lambda: collections.Counter())
tables = collections.defaultdict(lambda: [])
field_sizes = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

Fotypev = F.otype.v
Fmonadsv = F.monads.v
Fmin = F.minmonad.v
Fmax = F.maxmonad.v
Ftextv = F.g_word_utf8.v
Foccv = F.g_cons.v
Flexv = F.lex.v
Flanguagev = F.language.v
Ftrailerv = F.trailer_utf8.v
Fnumberv = F.number.v

dqf = outfile('etcbc4-lexicon.tsv')
dqf.write('{}\n'.format('\t'.join(x[2] for x in lex_fields)))

def compute_fields(lan, entry, lexfeats):
    cur_lex_values.clear()
    return tuple(compute_field(lan, entry, lexfeats, f) for f in lex_fields)

def compute_field(lan, entry, lexfeats, f):
    (source, method, name, transform, datatype, datasize, dataoption) = f
    val = None
    if method == 'lan': val = lan
    elif method == 'entry': val = entry
    elif method == 'id':
        val = '{}{}'.format(
            '1' if lan == 'hbo' else '2',
            entry.
                replace('>','A').
                replace('<','O').
                replace('[','v').
                replace('/','n').
                replace('=','i'),
        )
        lex_index[(lan, entry)] = val
    elif method =='lex':
        val = s_esc(lexfeats.get(source, ''))
        if transform != None and val in transform: val = transform[val]
    else: val = method(cur_lex_values[source])
    cur_lex_values[name] = val
    if name in field_limits['lexicon']:
        field_sizes['lexicon'][name] = max(len(val), field_sizes['lexicon'][name])
    return val

for lan in sorted(lex_entries):
    for entry in sorted(lex_entries[lan]):
        format_str = '({})'.format(','.join('{}' if f[4] == 'int' else "'{}'" for f in lex_fields))
        entry_info = compute_fields(lan, entry, lex_entries[lan][entry])
        dqf.write('{}\n'.format('\t'.join(str(x) for x in entry_info)))
        tables['lexicon'].append(format_str.format(
            *entry_info
        ))
dqf.close()

def do_verse(node):
    global cur_verse_node, cur_verse_info, max_len_text, max_len_xml
    if cur_verse_node != None:
        this_text = ''.join('{}{}'.format(x[0], x[1]) for x in cur_verse_info)
        this_xml = ''.join(
            '''<w m="{}" t="{}" l="{}">{}</w>'''.format(
                x[2], x[1].replace('\n', '&#xa;'), x[4], x[0]
            ) for x in cur_verse_info)
        field_sizes['verse']['text'] = max((len(this_text), field_sizes['verse']['text']))
        field_sizes['verse']['xml'] = max((len(this_xml), field_sizes['verse']['xml']))
        tables['verse'].append("({},{},{},{},{},'{}','{}')".format(
            cur_id['verse'], 
            cur_verse_first_m, 
            cur_verse_last_m, 
            cur_id['chapter'], F.verse.v(cur_verse_node), s_esc(this_text), s_esc(this_xml),
        ))
        for x in cur_verse_info:
            tables['word_verse'].append("({}, {}, '{}')".format(
                x[2], x[3], x[4]
            ))
        cur_verse_info = []
    cur_verse_node = node    

for node in NN():
    otype = Fotypev(node)
    if otype == 'word':
        if node in qeres:
            (text, trailer) = qeres[node]
        else:
            text = Ftextv(node)
            trailer = Ftrailerv(node)
        if trailer.endswith('ס') or trailer.endswith('פ'): trailer += ' '
        lex = Flexv(node)
        lang = Flanguagev(node)
        lid = lex_index.get((lang_map[lang], lex), None)
        if lid == None:
            lex_not_found[(lang_map[lang], lex)][Foccv(node)] += 1
        cur_verse_info.append((
            text,
            trailer,
            Fmonadsv(node), 
            cur_id['verse'],
            lid,
        ))
    elif otype == 'verse':
        do_verse(node)
        cur_id['verse'] += 1
        cur_verse_first_m = Fmin(node)
        cur_verse_last_m = Fmax(node)
    elif otype == 'chapter':
        do_verse(None)
        cur_id['chapter'] += 1
        tables['chapter'].append("({},{},{},{},{})".format(
            cur_id['chapter'], Fmin(node), Fmax(node), cur_id['book'], F.chapter.v(node),
        ))
    elif otype == 'book':
        do_verse(None)
        cur_id['book'] += 1
        name = F.book.v(node)
        field_sizes['book']['name'] = max((len(name), field_sizes['book']['name']))
        tables['book'].append("({},{},{},'{}')".format(
            cur_id['book'], Fmin(node), Fmax(node), s_esc(name),
        ))
    elif otype == 'clause_atom':
        cur_id['clause_atom'] += 1
        ca_num = Fnumberv(node)
        wordtexts = []
        for w in L.d('word', node):
            trsep = Ftrailerv(w)
            if trsep.endswith('ס') or trsep.endswith('פ'): trsep += ' '
            wordtexts.append(F.g_word_utf8.v(w) +trsep)
        text = ''.join(wordtexts)
        field_sizes['clause_atom']['text'] = max((len(text), field_sizes['clause_atom']['text']))
        tables['clause_atom'].append("({},{},{},{},{},'{}')".format(
            cur_id['clause_atom'], Fmin(node), Fmax(node), ca_num, cur_id['book'], s_esc(text),
        ))
do_verse(None)

for tb in sorted(field_limits):
    for fl in sorted(field_limits[tb]):
        limit = field_limits[tb][fl]
        actual = field_sizes[tb][fl]
        exceeded = actual > limit
        outp = sys.stderr if exceeded else sys.stdout
        outp.write('{:<5} {:<15}{:<15}: max size = {:>7} of {:>5}\n'.format(
            'ERROR' if exceeded else 'OK',
            tb, fl, actual, limit,
        ))

msg("Done")
if len(lex_not_found):
    sys.stderr.write('Text lexemes not found in lexicon: {}x\n'.format(len(lex_not_found)))
    for l in sorted(lex_not_found):
        sys.stderr.write('{} {}\n'.format(*l))
        for (o, n) in sorted(lex_not_found[l].items(), key=lambda x: (-x[1], x[0])):
            sys.stderr.write('\t{}: {}x\n'.format(o, n))
else:
    print('All lexemes have been found in the lexicon')


# In[8]:

print('\n'.join(tables['lexicon'][0:10]))
print('\n'.join(tables['clause_atom'][0:10]))


# # Extra word data
# 
# Now we fetch the data needed for representing rich hebrew text.
# 
# ## Passage index
# When we have found our objects, we want to indicate where they occur in the bible. In order to specify the passage of a node, we have to now in what verse a node occurs. In the next code cell we create a mapping from nodes of type sentence, clause, etc to nodes of type verse. From a verse node we can read off the passage information.
# 
# Conversely, we also construct an index from verses to nodes: given a verse, we make a list of all nodes belonging to that verse, in the canonical order.

# In[9]:

target_types = {
    'sentence', 'sentence_atom', 
    'clause', 'clause_atom', 
    'phrase', 'phrase_atom', 
    'subphrase',
}

def get_set(monads):
    monad_set = set()
    for rn in monads.split(','):
        bnds = rn.split('-', 1)
        if len(bnds) == 1:
            monad_set.add(int(bnds[0]))
        else: 
            monad_set |= set(range(int(bnds[0]), int(bnds[1]) + 1))
    return frozenset(monad_set)

def ranges(monadset):
    result = []
    cur_start = None
    cur_end = None
    for i in sorted(monadset):
        if cur_start == None:
            cur_start = i
            cur_end = i
        else:
            if i == cur_end + 1:
                cur_end += 1
            else:
                result.append((cur_start, cur_end))
                cur_start = i
                cur_end = i
    if cur_start != None:
        result.append((cur_start, cur_end))
    return result

def get_objects(vn):
    objects = set()
    for wn in L.d('word', vn):
        objects.add(wn)
        for tt in target_types:
            on = L.u(tt, wn)
            if on != None: objects.add(on)
    return objects


# # Fill the word info table with data

# In[10]:

msg("Generating word info data ...")
wordf = outfile('word_data.tsv')
#wordrf = outfile('word_r_data.tsv')
plainf = outfile('verse_plain.txt')
wordf.write('{}\n'.format('\t'.join('{}_{}'.format(f[2], f[1]) for f in word_fields)))
#wordrf.write('{}\t{}\t{}\t{}\n'.format('book', 'chapter', 'verse', '\t'.join('{}_{}'.format(f[2], f[1]) for f in word_fields)))
tables['word'] = []

if 'word' in field_sizes: del field_sizes['word']

def do_verse_info(verse):
    vlabel = '{} {}:{}'.format(F.book.v(verse), F.chapter.v(verse), F.verse.v(verse))
    wordf.write('!{}\n'.format(vlabel))
#    monads = verse_monads[verse]
    monads = {int(F.monads.v(w)) for w in L.d('word', verse)}
    
    (verse_startm, verse_endm) = (min(monads), max(monads))
#    objects = verse_node[verse]
    objects = get_objects(verse)
    words = [dict() for i in range(verse_startm, verse_endm + 1)]
    for w in words:
        for (otype, do_border) in (
            ('sentence', True), 
            ('sentence_atom', False), 
            ('clause', True), 
            ('clause_atom', False), 
            ('phrase', True),
            ('phrase_atom', False),
            ('subphrase', True),
            ('word', False),
        ):
            w['{}_{}'.format(otype, 'number')] = list()
            if do_border:
                w['{}_{}'.format(otype, 'border')] = set()
    nwords = len(words)
    subphrase_counter = 0
    word_nodes = []
    for n in objects:
        otype = F.otype.v(n)
        if otype == 'word': word_nodes.append(n)
        number_prop = '{}_{}'.format(otype, 'number')
        if otype != 'word' and not otype.endswith('_atom'):
            border_prop = '{}_{}'.format(otype, 'border')
        else:
            border_prop = None

        if otype == 'subphrase': subphrase_counter += 1
        elif otype in {'phrase', 'clause', 'sentence'}: subphrase_counter = 0
# Here was a bug: I put the subphrase_counter to 0 upon encountering anything else than a subphrase or a word.
# I had overlooked the half_verse, which can cut through a phrase
        this_info = {}
        this_number = None
        for f in word_fields:
            (method, name, typ) = (f[0], '{}_{}'.format(f[2], f[1]), f[3])
            if otype != f[2] or method == None: continue
            if method == 'id':
                value = subphrase_counter
            else:
                value = method(n)
                if typ == 'int': value = int(value)
            if name == number_prop:
                this_number = value
            else:
                this_info[name] = value
        if otype == 'word':
            target = words[this_number - verse_startm]
            target.update(this_info)
            target[number_prop].append(this_number)            
        else:
            these_ranges = ranges(get_set(F.monads.v(n)))
            nranges = len(these_ranges) - 1
            for (e,r) in enumerate(these_ranges):
                is_first = e == 0
                is_last = e == nranges
                right_border = 'rr' if is_first else 'r'
                left_border = 'll' if is_last else 'l'
                first_word = -1 if r[0] < verse_startm else nwords if r[0] > verse_endm else r[0] - verse_startm
                last_word = -1 if r[1] < verse_startm else nwords if r[1] > verse_endm else r[1] - verse_startm
                my_first_word = max(first_word, 0)
                my_last_word = min(last_word, nwords - 1)
                for i in range(my_first_word, my_last_word + 1):
                    target = words[i]
                    if not first_only[number_prop] or i == my_first_word:
                        target[number_prop].append(this_number)
                    for f in this_info:
                        if not first_only[name] or i == my_first_word:
                            words[i][f] = this_info[f]
                    if otype == 'subphrase':
                        if border_prop != None: words[i][border_prop].add('sy')
                if 0 <= first_word < nwords:
                    if border_prop != None: words[first_word][border_prop].add(right_border)
                if 0 <= last_word < nwords:
                    if border_prop != None: words[last_word][border_prop].add(left_border)
    wordtext = []
    for w in word_nodes:
        trsep = Ftrailerv(w)
        if trsep.endswith('ס') or trsep.endswith('פ'): trsep += ' '
        wordtext.append(F.g_word_utf8.v(w) +trsep)
    plainf.write("{}\t{}\n".format(
        vlabel, 
        ''.join(wt for wt in wordtext).replace('\n', '\\n'),
    ))
    for w in words:
        row = []
        rrow = []
        for f in word_fields:
            typ = f[3]
            name = '{}_{}'.format(f[2], f[1])
            value = w.get(name, 'NULL' if typ == 'int' else '')
            if f[1] == 'border':
                value = ' '.join(value)
            elif f[1] == 'number':
                value = ' '.join(str(v) for v in value)
            rrow.append(str(value).replace('\n', '\\n').replace('\t', '\\t'))
            if typ == 'int':
                value = str(value)
            else:
                if typ.endswith('char'):
                    lvalue = len(value)
                    curlen = field_sizes['word'][name]
                    if lvalue > curlen: field_sizes['word'][name] = lvalue
                value = "'{}'".format(s_esc(value))
            row.append(value)
        tables['word'].append('({})'.format(','.join(row)))
        wordf.write("{}\n".format('\t'.join(rrow)))
        #wordrf.write("{}\t{}\t{}\t{}\n".format(F.book.v(verse), F.chapter.v(verse), F.verse.v(verse),'\t'.join(rrow)))

for n in NN():
    if F.otype.v(n) == 'book':
        msg("\t{}".format(F.book.v(n)))
    elif F.otype.v(n) == 'verse':
        do_verse_info(n)

wordf.close()
#wordrf.close()
plainf.close()
msg("Done")


# In[12]:

# check whether the field sizes are not exceeded

tb = 'word'
for f in word_fields:
    (fl, typ, limit) = ('{}_{}'.format(f[2], f[1]), f[3], f[4])
    if typ != 'varchar': continue
    actual = field_sizes[tb][fl]
    exceeded = actual > limit
    outp = sys.stderr if exceeded else sys.stdout
    outp.write('{:<5} {:<15}{:<15}: max size = {:>7} of {:>5}\n'.format(
        'ERROR' if exceeded else 'OK',
        tb, fl, actual, limit,
    ))


# # SQL generation

# In[ ]:

limit_row = 2000

tables_head = collections.OrderedDict((
    ('book', 'insert into book (id, first_m, last_m, name) values \n'),
    ('chapter', 'insert into chapter (id, first_m, last_m, book_id, chapter_num) values \n'),
    ('verse', 'insert into verse (id, first_m, last_m, chapter_id, verse_num, text, xml) values \n'),
    ('clause_atom', 'insert into clause_atom (id, first_m, last_m, ca_num, book_id, text) values \n'),
    ('lexicon', 'insert into lexicon ({}) values \n'.format(', '.join(f[2] for f in lex_fields))),
    ('word', 'insert into word ({}) values \n'.format(', '.join('{}_{}'.format(f[2], f[1]) for f in word_fields))),
    ('word_verse', 'insert into word_verse (anchor, verse_id, lexicon_id) values \n'),
))

sqf = outfile('shebanq_passage{}.sql'.format(version))
sqf.write(text_create_sql)

msg('Generating SQL ...')
for table in tables_head:
    msg('\ttable {}'.format(table))
    start = tables_head[table]
    rows = tables[table]
    r = 0
    while r < len(rows):
        sqf.write(start)
        s = min(r + limit_row, len(rows))
        sqf.write(' {}'.format(rows[r]))
        if r + 1 < len(rows):
            for t in rows[r + 1:s]: sqf.write('\n,{}'.format(t))
        sqf.write(';\n')
        r = s
        
sqf.close()
msg('Done')


# In[ ]:



