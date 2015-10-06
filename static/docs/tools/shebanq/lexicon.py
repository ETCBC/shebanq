
# coding: utf-8

# <a href="http://laf-fabric.readthedocs.org/en/latest/" target="_blank"><img align="left" src="images/laf-fabric-xsmall.png"/></a>
# <a href="http://www.godgeleerdheid.vu.nl/etcbc" target="_blank"><img align="left" src="images/VU-ETCBC-xsmall.png"/></a>
# <a href="http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71" target="_blank"><img align="left"src="images/etcbc4easy-small.png"/></a>
# <a href="http://tla.mpi.nl" target="_blank"><img align="right" src="images/TLA-xsmall.png"/></a>
# <a href="http://www.dans.knaw.nl" target="_blank"><img align="right"src="images/DANS-xsmall.png"/></a>

# # The ETCBC lexicon files
# 
# We examine the ETCBC lexicon files, we check their internal consistency and their correspondence
# with the ETCBC4 database, 
# and finally we will add the lexicon as extra features to the ETCBC4 text database.
# 
# The lexical features of a lexeme are added to each word occurrence in the text that is associated with that lexeme.
# 
# Of course, this is redundant, but for text processing it is convenient. 
# Alternatively, we could transform this data to
# [LMF (Lexical Markup Framework)](http://www.lexicalmarkupframework.org) [ISO-24613:2008](http://www.iso.org/iso/catalogue_detail.htm?csnumber=37327) for usage next to the LAF version of the Hebrew Text Database.
# An introduction to LMF can be found on [Wikipedia](http://en.wikipedia.org/wiki/Lexical_Markup_Framework).
# [Generate schemas](https://tla.mpi.nl/relish/lmf/).
# See also [this paper (pdf)](http://www.lrec-conf.org/proceedings/lrec2014/pdf/154_Paper.pdf) by Menzo Windhouwer et. al.
# May be later.
# 
# # The ETCBC Ketiv-Qere files
# 
# In the Emdros export of the ETCBC database,
# only the *ketiv* representations are present, not the (vocalized)
# *qere* versions.
# However, we can include this data from a separate file.
# We include two features: 
# 
# * *qere* the fully vocalized qere in ETCBC transcription
# * *qtrailer* the material after a qere before the next word, also in ETCBC transcription
# 
# # Biblical languages
# Among the ETCBC data are lexicon files for the biblical languages.
# We want to put that data in LMF files, and put them to use in LAF-Fabric and SHEBANQ.
# 
# We have lexicon files for the following languages (given in [ISO 639-3 codes and names](http://www-01.sil.org/iso639-3/default.asp))
# 
# * ``hbo`` *Ancient Hebrew*
# * ``arc`` *Official Aramaic; Imperial Aramaic*
# * ``syc`` *Classical Syriac*
# 
# In the sequel we will consistently and exclusively refer to these languages by their ISO 639-3 abbreviations.
# For the ETCBC4 database we use ``hbo`` and ``arc`` only.
# 
# # Feature explanation
# 
# Here is a list of features encountered in the lexicon.
# Some of them correspond to features encountered in the text.
# 
# ## entry 
# corresponds to the ``lex`` feature of word occurrences.
# 
# ## vocalized lexeme
# ``vc``  looks like the ``g_lex`` feature of word occurrence, but they are not the same. The ``vc`` is an idealized (aka *paradigmatic*), pointed representation of the lexeme, which may or may not occur in the text. The ``g_lex`` is the realized lexeme in a concrete occurrence, of which it may be a part.
# 
# ## root
# ``rt`` does not correspond to a feature of word occurrences.
# It contains the abstract root of a lexeme, in the sense of the form from which the lexeme has been *derived*.
# 
# ## part of speech
# ``sp`` corresponds exactly to ``sp`` on word occurrences.
# 
# ## subpart of speech (lexical set)
# ``ls`` corresponds to exactly to ``ls`` on word occurrences.
# 
# ## gender
# ``gn`` corresponds to ``gn`` on word occurrences, except for words whose gender is not lexically determined such as verbs and adjectives. The policy is to include this feature in the lexicon only when the gender is not obvious from the set of its textual occurrences.
# 
# ## number
# ``nu`` corresponds to ``nu`` on word occurrences, but in general number is not lexically determined.
# 
# ## person
# ``ps`` corresponds to ``ps`` on word occurrences, but in general person is not lexically detemined.
# It occurs on a small number of ``pspr`` s in the lexicon.
# 
# ## state
# ``st`` corresponds to ``st`` on word occurrences. It is only marked for a few ``nmpr`` s in the lexicon.
# 
# ## reference type
# ``sm``  does not correspond to a textual feature. It is the reference type of proper nouns and personal pronouns (rarely), and consists of a comma separated list of the following values:
# 
# * ``gens`` people or tribe name
# * ``mens`` month name
# * ``pers`` person name
# * ``ppde`` possible demonstrative pronoun, occurs only for personal pronouns
# * ``topo`` place name
# 
# ## comment or corrections
# ``co`` does not correspond to any feature on word occurrences. Comments are used to express alternatives for the information entered. Comments are very rare in the lexicon.
# 
# ## kb
# ``kb`` unclear. In *arc* there is one occurrence containing a transliterated words, in *hbo* there are a few occurrences containing a different value for ``sp``.
# 
# ## fc
# ``fc`` unclear.
# 
# # Lexicon data
# 
# We add the lexicon data as extra features to the ETCBC4 database.
# 
# For every word, we add *lexical* features, i.e. features that are obtained from looking up the word in the lexicon and then reading off extra attributes from the lexical entry.
# 
# We add these features into the ``etcbc4`` annotation space, with label ``lex``.
# These are the extra features:
# 
# * **lid** a fresh id, to be used in applications, unique over **entryid** and **lan**
# * **lan** the language of the entry, in ISO 639-3 abbreviation
# * **entryid** (= ``entry``) the string used as entry in the lexicon and as value of the ``lex`` feature in the text
# * **entry** the unpointed transliteration (= **entryid** without disambiguation marks)
# * **entry_heb** the unpointed hebrew representation, obtained by untransliterating **entry**
# * (shortly) **g_entry** (= ``vc``) the pointed transliteration, without disambiguation marks
# * (shortly) **g_entry_heb** the pointed hebrew representation, obtained by untransliterating **g_entry**
# * (shortly) **root** (= ``rt``) the root
# * **gloss** (= ``gl``) the gloss
# * **pos** (= ``sp``) the part of speech
# * **nametype** (= ``sm``) the type of named entity
# * **subpos** (= ``ls``) subtype of part of speech (aka *lexical set*)

# In[1]:

import collections
import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.extra import ExtraData
from etcbc.lib import Transcription
fabric = LafFabric()


# ## Create annotations from lexicon file

# In[4]:

source = 'etcbc'
if 'version' not in locals(): version = '4b'


# In[2]:

API=fabric.load(source+version, '--', 'lexicon', {
    "xmlids": {"node": True, "edge": False},
    "features": ('''
        oid otype label
        g_word g_word_utf8 g_cons language lex lex_utf8 g_lex g_lex_utf8
        sp ls gn nu ps st    ''',
    '''
    '''),
    "prepare": prepare,
}, verbose='NORMAL')
exec(fabric.localnames.format(var='fabric'))


# # Read and check the lexical files
# 
# First we read the lexicon, and perform some internal consistency checks, e.g. whether there are duplicate lexical entries.

# In[3]:

langs = {'hbo', 'arc'}
lex_base = dict((lan, '{}/{}/{}.{}{}'.format(API['data_dir'], 'lexicon', lan, source, version)) for lan in langs)
lang_map = {
    'Hebrew': 'hbo',
    'Aramaic': 'arc',
}

def read_lex(lan):
    lex_infile = open(lex_base[lan], encoding='utf-8')
    lex_outfile = outfile('{}.txt'.format(lan))
    lex_errfile = outfile('{}.err.txt'.format(lan))

    lex_items = {}
    ln = 0
    e = 0
    for line in lex_infile:
        ln += 1
        line = line.rstrip()
        line = line.split('#')[0]
        if line == '': continue
        (entry, featurestr) = line.split(sep=None, maxsplit=1)
        entry = entry.strip('"')
        if entry in lex_items:
            lex_errfile.write('duplicate lexical entry {} in line {}.\n'.format(entry, ln))
            e += 1
            continue
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
                    lex_errfile.write('feature without value for lexical entry {} in line {}: {}\n'.format(entry, ln, feature))
                    e += 1
                    continue
            (key, value) = comps
            value = value.replace(chr(254), ':')
            if key in features:
                lex_errfile.write('duplicate feature for lexical entry {} in line {}: {}={}\n'.format(entry, ln, key, value))
                e += 1
                continue
            features[key] = value
        if 'sp' in features and features['sp'] == 'verb':
            if 'gl' in features:
                gloss = features['gl']
                if gloss.startswith('to '):
                    features['gl'] = gloss[3:]
        lex_items[entry] = features
        lex_outfile.write('{}\t{}\n'.format(entry, features))
        
    lex_infile.close()
    lex_outfile.close()
    lex_errfile.close()
    msgstr = "Lexicon {}: there w".format(lan) + ('ere {} errors'.format(e) if e != 1 else 'as 1 error')
    print(msgstr)
    return lex_items

msg("Reading lexicon ...")
lex_entries = dict((lan, read_lex(lan)) for lan in sorted(langs))
for lan in sorted(lex_entries):
    print('Lexicon {} has {:>5} entries'.format(lan, len(lex_entries[lan])))
msg("Done")


# # Gather the lexemes from the etcbc4 database
# 
# We inspect all word occurrences of the etcbc4 database, inspect their language and lexeme values, and construct sets of lexemes that belong to each of the two languages, ``hbo`` and ``arc``.

# In[4]:

lex_text = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: set())))
do_value_compare = {'sp', 'ls', 'gn', 'ps', 'nu', 'st'}
text_value_set = collections.defaultdict(lambda: set())
node_lex = {}

msg("Reading ETCBC database {}{} ...".format(source, version))
text_langs = set()
for n in F.otype.s('word'):
    lan = lang_map[F.language.v(n)]
    text_langs.add(lan)
    lex = F.lex.v(n)
    node_lex[n] = (lan,lex)
    lex_text[lan][lex]['sp'].add(F.sp.v(n))
    lex_text[lan][lex]['ls'].add(F.ls.v(n))
    lex_text[lan][lex]['gn'].add(F.gn.v(n))
    lex_text[lan][lex]['nu'].add(F.nu.v(n))
    lex_text[lan][lex]['ps'].add(F.ps.v(n))
    lex_text[lan][lex]['vc'].add(F.g_lex.v(n))
    for p in do_value_compare:
        text_value_set[p].add(F.item[p].v(n))        

tf = outfile('text_lexemes.txt')
for lan in sorted(lex_text):
    for lex in sorted(lex_text[lan]):
        tf.write('{} "{}"\n'.format(lan, lex))
tf.close()
msg("Done")
for lan in sorted(lex_text):
    print('Language {} has {:>5} lexemes in the {}{} text'.format(lan, len(lex_text[lan]), source, version))


# # More checks
# 
# We check the following matters.
# 
# ## Intersection between Hebrew and Aramaic
# 
# Are there entries that are Hebrew and Aramaic?
# 
# We check 
# * whether the etcbc4 database has marked some lexemes belonging to ``hbo`` as well as belonging to ``arc``
# * whether the lexica for ``hbo`` and ``arc`` share lexeme entries
# * whether the lexical intersection of ``hbo`` and ``arc`` is equal to the textual intersection of ``hbo`` and ``arc``.

# In[5]:

arc_lex = set(lex_entries['arc'])
hbo_lex = set(lex_entries['hbo'])

arc_text = set(lex_text['arc'])
hbo_text = set(lex_text['hbo'])

hbo_and_arc_text = arc_text & hbo_text
hbo_and_arc_lex = arc_lex & hbo_lex

lex_min_text = hbo_and_arc_lex - hbo_and_arc_text
text_min_lex = hbo_and_arc_text - hbo_and_arc_lex


print('The intersection of hbo and arc in the etcbc4 text contains {} lexemes'.format(len(hbo_and_arc_text)))
print('The intersection of hbo and arc in the lexicon     contains {} lexemes'.format(len(hbo_and_arc_lex)))
print("Lexemes in the lexical intersection of hbo and arc but not in the textual intersection: {}x: {}".format(
    len(lex_min_text), lex_min_text)
)
print("Lexemes in the textual intersection of hbo and arc but not in the lexical intersection: {}x: {}".format(
    len(text_min_lex), text_min_lex)
)


# ## Match between lexicon and text
# Let us now check whether all lexemes in the text occur in the lexicon and vice versa.

# In[6]:

arc_text_min_lex = arc_text - arc_lex
arc_lex_min_text = arc_lex - arc_text

hbo_text_min_lex = hbo_text - hbo_lex
hbo_lex_min_text = hbo_lex - hbo_text

for (myset, mymsg) in (
    (arc_text_min_lex, 'arc: lexemes in text but not in lexicon'),
    (arc_lex_min_text, 'arc: lexemes in lexicon but not in text'),
    (hbo_text_min_lex, 'hbo: lexemes in text but not in lexicon'),
    (hbo_lex_min_text, 'hbo: lexemes in lexicon but not in text'),
):
    print('{}: {}x{}'.format(mymsg, len(myset), '' if not myset else '\n\t{}'.format(', '.join(sorted(myset)))))


# # Usability as identifier
# 
# We examine how the ``lex``feature can be transformed in an url friendly identifier.
# This is important, because theis feature has the potential of identifying lexemes across versions.
# 
# It turns out as follows:
# 
# * we need a length or at least 15
# * there are no spaces
# * most characters are ``A-Z``, except for `` < > _ [ / = ``
# 
# This is what we do:
# 
# * let us be safe and allocate a varchar(32)
# * the ``>`` is an alef, we translate it to ``a``
# * the ``<`` is an ayin, we translate it to ``y``
# * the ``/`` denotes a noun, we translate it to ``n``
# * the ``[`` denotes a verb, we translate it to ``v``
# * the ``=`` is for disambiguation, we translate it to ``0``
# * we prepend a language identifier, ``1`` for Hebrew, ``2`` for aramaic. 

# In[7]:

max_len = 0
chars = collections.Counter()
for n in F.otype.s('word'):
    lex = F.lex.v(n)
    if len(lex) > max_len: max_len = len(lex)
    for c in lex:
        chars[c] += 1
print('max len = {}'.format(max_len))
for c in sorted(chars):
    print('{} : {:>7} x'.format(c, chars[c]))


# ## Feature richness
# 
# Which features do the entries have, and what percentage of the entries has those features?

# In[8]:

feature_count = collections.defaultdict(lambda: collections.Counter())
inspect_prop = collections.defaultdict(
    lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: collections.Counter()))
)
lex_value_set = collections.defaultdict(lambda: set())

close_inspect = {'sp', 'sm', 'ls', 'gn', 'ps', 'nu', 'st'} # , 'co', 'kb', 'fc'

for lan in lex_entries:
    entries = lex_entries[lan]
    for entry in entries:
        features = entries[entry]
        for feature in features:
            feature_count[lan][feature] += 1
        for p in close_inspect:
            if p in features:
                inspect_prop[lan][p][features[p]][features['sp']] += 1
        if lan != 'syc':
            for p in do_value_compare:
                if p in features:
                    lex_value_set[p].add(features[p])

for lan in feature_count:
    nentries = len(lex_entries[lan])
    for feature in feature_count[lan]:
        fv = feature_count[lan][feature]
        feature_count[lan][feature] = fv * 100 / nentries

print("Feature occurrences in the lexicon")
for lan in sorted(feature_count):
    feature_spec = '\n'.join('\t{:<8}: {:>6.2f}%'.format(f, v) for (f,v) in sorted(feature_count[lan].items(), key=lambda x: (-x[1], x[0])))
    print("{}\n{}\t".format(lan, feature_spec))


# In[9]:

print("Detail feature values and occurrences")
for lan in sorted(inspect_prop):
    print("{}\n".format(lan))
    for p in sorted(inspect_prop[lan]):
        print("\t{}\n".format(p))
        for value in sorted(inspect_prop[lan][p]):
            inspect_spec = '\n'.join('\t\t\t{:<6}: {:>3}x'.format(f, v) for (f,v) in sorted(
                inspect_prop[lan][p][value].items(), key=lambda x: (-x[1], x[0])
            ))
            print("\t\t{}\n{}\t".format(value, inspect_spec))


# ## Consistency of text features
# 
# Multiple occurrences in the text point to the same lexeme. 
# Some properties of those occurrences are in fact properties of the lexeme, e.g. the part of speech.
# 
# The question arises: is the property assigned to the word occurrences in such a way that all occurrences of the same lexeme have the same value for that property?
# 
# We will see that this is in general not the case.
# There are features, that have a definition in the lexicon, but that can be overridden on word occurrences.
# 
# However, some features are more consistent than others: the features **pos** (=``sp``), **subpos** (= ``ls``), **gender**.
# 
# It becomes also clear that the lexical property **g_entry** (= ``vc``) (aka *vocalized lexeme*) is mostly different from the
# the textual feature **g_lex** (aka *graphical lexeme*).
# The output file *inconsistent.csv* shows exactly what is going on.

# In[10]:

consistent_props = {'sp', 'ls', 'gn', 'vc'}
variable_gender = {'verb', 'adjv'}

exceptions = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
exceptions_gn = collections.defaultdict(lambda: collections.Counter())

incons = outfile('inconsistent.csv')
for lan in sorted(lex_text):
    lexemes = lex_text[lan]
    for lexeme in sorted(lexemes):
        properties = lexemes[lexeme]
        for prop in consistent_props:
            if prop in properties:
                values = properties[prop]
                psp = list(properties['sp'])[0]
                if len(values) > 1:
                    if prop == 'gn':
                        if (len(set(properties['sp']) & variable_gender) != 0): continue
                        exceptions_gn[lan][psp] += 1
                    exceptions[lan][prop].add(lexeme)
                    incons.write('"{}";"{}";"{}";"{}";{};"{}"\n'.format(lan, prop, lexeme, psp, len(values), '";"'.join(values)))
incons.close()
for lan in sorted(text_langs):
    print("{}\n".format(lan))
    for prop in sorted(consistent_props):
        extra = ''
        if prop == 'gn':
            for psp in exceptions_gn[lan]:
                extra += '\n{}{}: {}x'.format(' ' * 8, psp, exceptions_gn[lan][psp])
        print("{}{:<8}: {:>4} inconsistent lexemes{}".format(' ' * 4, prop, len(exceptions.get(lan, {}).get(prop, set())), extra))        


# ## Consistency of feature values between lexicon and text
# 
# Are the *values* of features used in the text database consistent with the values used in the lexicon?
# 
# If not, we will apply a value transformation that harmonizes the values in lexical entries with those in textual features.
# We adapt the lexical values to the textual ones. We do this only for features whose value domains are enumerations.

# In[11]:

for p in do_value_compare:
    print(p)
    text_not_lex = sorted(text_value_set[p] - lex_value_set[p])
    lex_not_text = sorted(lex_value_set[p] - text_value_set[p])
    print('\tin text and not in lex: {}: {}'.format(len(text_not_lex), text_not_lex))
    print('\tin lex and not in text: {}: {}'.format(len(lex_not_text), lex_not_text))


# # Checking lex_utf8
# 
# There are two ways to get the unpointed lexeme in Unicode form:
# 
# * use the ``lex_utf8`` feature
# * use the ``lex`` feature, strip the disambiguation marks at the end, and un-transliterate.
# 
# We check whether they yield the same results.
# 
# As a preliminary check, we check whether there is a 1-1 correspondence between the ``lex`` and ``lex_utf8`` features.

# In[12]:

def strip_id(entryid):
    return entryid.rstrip('/[=')

def to_heb(translit):
    return Transcription.to_hebrew(Transcription.suffix_and_finales(translit)[0])


lex = collections.defaultdict(lambda: set())
for n in F.otype.s('word'):
    lexstrip = strip_id(F.lex.v(n))
    lexustrip = strip_id(F.lex_utf8.v(n))
    lex[lexstrip].add(lexustrip)
print('There are {} lexemes, ignoring homonyms'.format(len(lex)))
disc = set()
for lx in lex:
    if len(lex[lx]) > 1: disc.add(lx)
if len(disc) == 0:
    print('There is a 1-1 correspondence between lex/strip and lex_utf8')
else:
    print('There are a {} lex/strip values with multiple lex_utf8 values'.format(len(disc)))
    for lx in disc:
        print('{} has {}'.format(lx, lex[lx]))


# # Composing a lexical data file
# 
# The specification in ``lex_fields`` below specifies the lexicon fields in the intended order.
# It contains instructions how to construct the field values from the lexical information obtained from the lexicon files.
# 
#     (source, method, name, transformation table, data type, data size, data options)
# 
# ## source 
# May contain one of the following:
# 
# * the name of a lexical feature as shown in the lexicon files, such as ``sp``, ``vc``.
# * None. 
#   In this case, **method** is a code that triggers special actions, such as getting an id or something that is available to the   program that fills the lexicon table
# * the name of an other field as shown in the **name** part of the specification. 
#   In this case, **method** must be a function, defined else where, that takes the value of that other field as argument. 
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
# 
# ## name
# The name of the field in the to be constructed annotation file.

# In[13]:

lex_fields = (
    (None, 'id', 'id', None),
    (None, 'lan', 'lan', None),
    (None, 'entry', 'entryid', None),
    ('entryid', strip_id, 'entry', None),
    ('entry', to_heb, 'entry_heb', None),
    ('vc', 'lex', 'g_entry', None),
    ('g_entry', to_heb, 'g_entry_heb', None),
    ('rt', 'lex', 'root', None),
    ('sp', 'lex', 'pos', None),
    ('sm', 'lex', 'nametype', None),
    ('ls', 'lex', 'subpos', None),
    ('gl', 'lex', 'gloss', None),
)

cur_lex_values = {}

def compute_fields(lan, entry, lid, lexfeats):
    cur_lex_values.clear()
    return tuple(compute_field(lan, entry, lid, lexfeats, f) for f in lex_fields)

def compute_field(lan, entry, lid, lexfeats, f):
    (source, method, name, transform) = f
    val = None
    if method == 'lan': val = lan
    elif method == 'entry': val = entry
    elif method == 'id': val = lid
    elif method =='lex':
        val = lexfeats.get(f[0], '')
        if transform != None and val in transform: val = transform[val]
    else: val = method(cur_lex_values[f[0]])
    cur_lex_values[f[2]] = val
    return val

lex_index = {}
cur_id = -1
for lan in sorted(lex_entries):
    for entry in sorted(lex_entries[lan]):
        cur_id += 1
        entry_info = compute_fields(lan, entry, cur_id, lex_entries[lan][entry])
        lex_index[(lan, entry)] = entry_info


# ## Deliver lexical data

# In[14]:

def get_lex(dummy):
    msg('Preparing lex data')
    data = []
    for n in sorted(node_lex):
        this_info = lex_index[node_lex[n]]
        data.append((n,) + this_info)
    msg('{} words'.format(len(data)))
    return data


# # Phonetic transcription
# 
# We load the output of the phono notebook, which has provided for each word node a phonetc transcription.

# In[15]:

def get_phono(file_name):
    msg('Reading phonetic transcriptions')
    phonos = []
    phono_file = open(file_name)
    for line in phono_file:
        (node, wordph, sep) = line[0:-1].split('\t')
        if sep == '+': continue
        phonos.append((int(node), wordph, sep))
    phono_file.close()
    msg('{} words'.format(len(phonos)))
    return phonos


# # Read and check the ketiv qere files
# 
# ## Make a verse index
# 
# De ketiv qere files use a particular form of verse labels.
# We have to map them to the corresponding verse nodes.

# In[16]:

msg("Making mappings between verse labels in KQ and verse nodes in LAF")
vlab2vnode = {}
for vs in F.otype.s('verse'):
    lab = F.label.v(vs)
    vlab2vnode[lab] = vs
msg("{} verses".format(len(vlab2vnode)))


# ## Method to read kq data

# In[17]:

def get_kq(kq_file):
    msg("Reading Ketiv-Qere data")

    info = collections.defaultdict(lambda: [])
    not_found = set()
    missing = collections.defaultdict(lambda: [])
    missed = collections.defaultdict(lambda: [])

    error_limit = 10

    kq_handle = open(kq_file)

    ln = 0
    can = 0
    cur_label = None
    for line in kq_handle:
        ln += 1
        can += 1
        vlab = line[0:10]
        fields = line.rstrip('\n')[10:].split()
        (ketiv, qere) = fields[0:2]
        (qtrim, qtrailer) = Transcription.suffix_and_finales(qere)
        vnode = vlab2vnode.get(vlab, None)
        if vnode == None:
            not_found.add(vlab)
            continue
        info[vnode].append((ketiv, qtrim, qtrailer))        
    kq_handle.close()
    msg("Read {} ketiv-qere annotations".format(ln))

    data = []
    for vnode in info:
        wlookup = collections.defaultdict(lambda: [])
        wvisited = collections.defaultdict(lambda: -1)
        wnodes = L.d('word', vnode)
        for w in wnodes:
            gw = F.g_word.v(w)
            if '*' in gw:
                gw = F.g_cons.v(w)
                if gw == '': gw = '.'
                wlookup[gw].append(w)
        for (ketiv, qere, qtrailer) in info[vnode]:
            wvisited[ketiv] += 1
            windex = wvisited[ketiv]
            ws = wlookup.get(ketiv, None)
            if ws == None or windex > len(ws) - 1:
                missing[vnode].append((windex, ketiv, qere))
                continue
            w = ws[windex]
            qere_u = Transcription.to_hebrew(qere)
            qtrailer_u = Transcription.to_hebrew(qtrailer)
            data.append((w, ketiv, qere_u, qtrailer_u))
        for ketiv in wlookup:
            if ketiv not in wvisited or len(wlookup[ketiv]) - 1 > wvisited[ketiv]:
                missed[vnode].append((len(wlookup[ketiv]) - (wvisited.get(ketiv, -1) + 1), ketiv))
    msg("Parsed {} ketiv-qere annotations".format(len(data)))

    if not_found:
        msg("Could not find {} verses: {}".format(len(not_found), sorted(not_found)))
    else:
        msg("All verses entries found in index")
    if missing:
        msg("Could not locate ketivs in the text: {} verses".format(len(missing)))
        e = 0
        for vnode in sorted(missing):
            if e > error_limit: break
            vlab = F.label.v(vnode)
            for (windex, ketiv, qere) in missing[vnode]:
                e += 1
                if e > error_limit: break
                print('NOT IN TEXT: {:<10} {:<20} #{} {}'.format(vlab, ketiv, windex, qere))
    else:
        msg("All ketivs found in the text")
    if missed:
        msg("Could not lookup qeres in the data: {} verses".format(len(missing)))
        e = 0
        for vnode in sorted(missed):
            if e > error_limit: break
            vlab = F.label.v(vnode)
            for (windex, ketiv) in missed[vnode]:
                e += 1
                if e > error_limit: break
                print('NOT IN DATA: {:<10} {:<20} #{}'.format(vlab, ketiv, windex))
    else:
        msg("All ketivs found in the data")
    return [(x[0], x[2], x[3]) for x in data]


# # Compose the annotation package

# In[18]:

lex = ExtraData(API)

ph_base = '{}/{}.{}{}'.format('ph', 'phono', source, version)
kq_base = '{}/{}.{}{}'.format('kq', 'kq', source, version)

msg("Writing annotation package ...")
lex.deliver_annots(
    'lexicon', 
    {'title': 'Lexicon lookups, phonetic transcription, ketiv-qere', 'date': '2015'},
    [
        (ph_base, 'ph', get_phono, (
            ('etcbc4', 'ph', 'phono'),
            ('etcbc4', 'ph', 'phono_sep'),
        )),
        (kq_base, 'kq', get_kq, (
            ('etcbc4', 'kq', 'g_qere_utf8'),
            ('etcbc4', 'kq', 'qtrailer_utf8'),
        )),
        ('lexicon/lex_data', 'lex', get_lex, (
            ('etcbc4', 'lex', 'id'),
            ('etcbc4', 'lex', 'lan'),
            ('etcbc4', 'lex', 'entryid'),
            ('etcbc4', 'lex', 'entry'),
            ('etcbc4', 'lex', 'entry_heb'),
            ('etcbc4', 'lex', 'g_entry'),
            ('etcbc4', 'lex', 'g_entry_heb'),
            ('etcbc4', 'lex', 'root'),
            ('etcbc4', 'lex', 'pos'),
            ('etcbc4', 'lex', 'nametype'),
            ('etcbc4', 'lex', 'subpos'),
            ('etcbc4', 'lex', 'gloss'),
        )),
    ]
)
msg("Done")


# ## Checking: loading the new features

# In[5]:

API=fabric.load(source+version, 'lexicon', 'gloss', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype
        book chapter verse
        g_cons_utf8 g_word_utf8 g_word lex g_entry gloss
        phono phono_sep
        g_qere_utf8 qtrailer_utf8
    ''',
    '''
    '''),
}, verbose='NORMAL',compile_annox=True)
exec(fabric.localnames.format(var='fabric'))


# ## Making an interlinear glossed text

# In[21]:

msg("Making interlinear glossed text ...")

trans_fname = 'glossed{}.txt'.format(version)
trans_file = outfile(trans_fname)
cur_label = None
cur_words = []

(s_len, sg, se, sv, sw, sh, sp) = (8,
        'gloss = ', 
        'lexeme= ',
        'voclex= ',
        'trans = ',
        'hebrew= ',
        'phono = ',
)

LL = 120

def set_verse():
    (first, cur_len, cg, ce, cv, cw, ch, cp) = (True, s_len, sg, se, sv, sw, sh, sp)

    def set_line():
        nonlocal first, cur_len, cur_len, cg, ce, cv, cw, ch, cp
        if cur_len != s_len:
            trans_file.write('{}\n'.format(('=' if first else '-') * cur_len))
            for l in (ch, cp, cw, cv, ce, cg):
                trans_file.write('{}\n'.format(l))
        (first, cur_len, cg, ce, cv, cw, ch, cp) = (False, s_len, sg, se, sv, sw, sh, sp)

    for n in cur_words:
        h = F.g_word_utf8.v(n)
        q = F.g_qere_utf8.v(n)
        if q != None:
            h = '*{}'.format(q)
        (g, e, v, w, p) = (F.gloss.v(n), F.lex.v(n), F.g_entry.v(n), F.g_word.v(n), F.phono.v(n))
        (lg, le, lv, lw, lh, lp) = tuple(len(x) for x in (g, e, v, w, h, p))
        lb = max((lg, le, lv, lw, lh, lp))
        if cur_len + lb + 1 > LL: set_line()
        cur_len += lb + 1
        fmtstr = '{{:<{}}}|'.format(lb)
        rfmtstr = '{{:>{}}}|'.format(lb)
        cg += fmtstr.format(g)
        ce += fmtstr.format(e)
        cv += fmtstr.format(v)
        cw += fmtstr.format(w)
        ch += rfmtstr.format(h)
        cp += fmtstr.format(p)
        cur_len += 1
    set_line()
    cur_words.clear()

for n in NN():
    otype = F.otype.v(n)
    if otype == 'verse':
        set_verse()
        cur_label = '{} {}:{}'.format(F.book.v(n), F.chapter.v(n), F.verse.v(n))
        trans_file.write('\n{}\n'.format(cur_label))
    elif otype == 'word':
        cur_words.append(n)
set_verse()

trans_file.close()

i = 0
inf = infile(trans_fname)
for line in inf:
    i += 1
    if i > 26: break
    print(line)
inf.close()
    
msg("Done")


# In[ ]:



