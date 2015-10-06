
# coding: utf-8

# <a href="http://laf-fabric.readthedocs.org/en/latest/" target="_blank"><img align="left" src="images/laf-fabric-xsmall.png"/></a>
# <a href="http://www.godgeleerdheid.vu.nl/etcbc" target="_blank"><img align="left" src="images/VU-ETCBC-xsmall.png"/></a>
# <a href="http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71" target="_blank"><img align="left"src="images/etcbc4easy-small.png"/></a>
# <a href="http://tla.mpi.nl" target="_blank"><img align="right" src="images/TLA-xsmall.png"/></a>
# <a href="http://www.dans.knaw.nl" target="_blank"><img align="right"src="images/DANS-xsmall.png"/></a>

# # Phonetic Transliteration of Hebrew Masoretic Text

# # Frequently asked questions
# 
# Q: *What is the use of a phonetic transliteration of the Hebrew Bible? What can anyone wish beyond the careful, meticulous Masoretic system of consonants, vowels and accents?*
# 
# A: Several things:
# 
# * the Hebrew Bible may be subject of study in various fields,
#   where the people involved do not master the Hebrew script;
#   a phonetic transcription removes a hurdle for them.
# * in computational linguistics there are many tools that deal with written language in latin alphabets;
#   even a simple task as getting the consonant-vowel pattern of a word is unnecessarily complicated
#   when using the Hebrew script.
# * in phonetics and language learning theory, it is important to represent the sounds without being burdened
#   by the idiosyncracies of the writing system and the spelling.
#   
# Q: *But surely, there already exist transliterations of Hebrew? Why not use them?*
# 
# Here are a few pragmatic reasons:
# 
# * we want to be able to *compute* a transliteration based upon our own data;
# * we want to gain insight in to what extent the transliteration can be purely rule-based, and to what extent
#   it depends on lexical information that you just need to know;
# * we want to make available a well documented transliteration, that can be studied, borrowed and improved by others.
# 
# Q: *But how **good** is your transliteration?*
# 
# we do not know, ..., yet. A few remarks though:
# 
# * we have applied most of the *rules* that we could find in Hebrew grammars;
# * we have suspended some of the rules for some verb paradigms where it is known that they lead to incorrect results
# * where the rules did not suffice, we have searched the corpus for other occurrences of the same word, to get clues;
# * where we knew that clues pointed in the wrong direction, we have applied a list of exceptions (currently a list of only the word בָּתִּֽים (\*bottˈîm => bāttˈîm) 
# * we have a fair test set with critical cases that all pass
# * we have a few tables of all cases where the algorithm has made corpus based decisions and lexical decisions
# * we are open for your corrections: login into [SHEBANQ](https://shebanq.ancient-data.org), go to a passage with         offending phonetic transliteration, and make a manual note. **Tip:** Give that note the keyword ``phono``, then we
#   will collect them.
# 
# Q: *To me, this is not entirely satisfying.*
# 
# A: Fair enough. Consider jumping to [Bible Online Learner](http://bibleol.3bmoodle.dk/text/show_text),
# where they have built in a pretty good transliteration, based on a different method of rule application. It is documented in an article by Nicolai Winther-Nielsen:
# [Transliteration of Biblical Hebrew for the Role-Lexical Module](http://www.see-j.net/index.php/hiphil/article/view/62) 
# and additional information can be found in Claus Tøndering's
# [Bible Online Learner, Software on Github](https://github.com/EzerIT/BibleOL).
# See also [Lex: A software project for linguists](http://www.see-j.net/index.php/hiphil/article/view/60/56).
# 
# We are planning to conduct an automatic comparison of both transliteration schemes over the whole corpus.
# 
# Q: *Who is the **we**?*
# 
# That is the author of this notebook, [Dirk Roorda](mailto:dirk.roorda@dans.knaw.nl), working together with Martijn Naaijer and getting input from Nicolai Winther-Nielsen and Wido van Peursen.

# # Overview of the results
# 
# 1. The main result is a python function ``phono(``*etcbc_original*``, ...): ``*phonetic transliteration*.
# 1. Showcases and tests: how the function solves particular classes of problems.
#    The *cases* file shows a set of cases that have been generated in the last run.
#    
#    The *tests* files show a prepared set of cases, against which to test new versions of the algorithm.
#    1. [mixed](mixed4b.html)
#       with logfile [mixed_debug](mixed_debug4b.txt).
#    1. [qamets_nonverb cases](qamets_nonverb_cases4b.html) and [qamets_nonverb tests](qamets_nonverb_tests4b.html)
#       with logfile [qamets_nonverb_tests_debug](qamets_nonverb_tests_debug4b.txt). 
#       The result of searching the corpus for related occurrences and 
#       having them vote for qatan/gadol interpretation of the qamets.
#    1. [qamets_verb cases](qamets_verb_cases4b.html) and [qamets_verb tests](qamets_verb_tests4b.html)
#       with logfile [qamets_verb_tests_debug](qamets_verb_tests_debug4b.txt).
#       The result of suppressing the qatan interpretation of the qamets regardless of accent
#       for a definite set of *verb forms*.
#    1. [qamets_prs cases](qamets_prs_cases4b.html) and [qamets_prs tests](qamets_prs_tests4b.html)
#       with logfile [qamets_prs_tests_debug](qamets_prs_tests_debug4b.txt).
#       The result of suppressing the qatan interpretation of the qamets in *pronominal suffixes*.
# 1. A [plain text](combi4b.txt) with the complete text in ETCBC transliteration and phonetic transcription,
#    verse by verse.

# # Overview of the method
# 
# ## Highlevel description
# 
# 1. **ETCBC transliteration**
#    Our starting point is the ETCBC full transliteration of the Hebrew Masoretic text.
#    This transliteration is in 1-1 correspondence with the Masoretic text, including all vowels and accents.
# 1. **Grammar rules** 
#    We have implemented the rules we find in grammars of Hebrew about long and short qamets, mobile and silent schwa,
#    dagesh, and mater lectionis. 
#    The implementation takes the form of a row of *regular expressions*,
#    where we transliterate targeted pieces of the original.
#    These regular expressions are exquisitely formulated, and must be applied in the given order.
#    *Beware:* Seemingly innocent modifications in these expressions or in the order of application,
#    may ruin the transcription completely.
# 1. **Qamets puzzles: verbs**
#    In many verb forms the grammar rules would dictate that a certain qamets is qatan while in fact it is gadol.
#    In most cases this is caused by the fact that no accent has been marked on the syllable that carries the
#    qamets in question. There is a limited set of verb paradigms where this occurs.
#    We detect those and suppress qamets qatan interpretation for them.
# 1. **Qamets puzzles: non-verbs**
#    There are quite a few non-verb occurrences where the accent pattern of a word invites a qamets to become
#    qatan, that is, by the grammar rules. 
#    Yet, other occurrences of the same lexeme have other accent patterns, and
#    lead to a gadol interpretation of the same qamets. 
#    In this case we count the unique cases in favour of gadol versus qatan, and let the majority decide for all 
#    occurrences. In cases where we know that the majority votes wrong, we have intervened.
#    
# ### Qamets work hypothesis
# Note, that in the the *non-verb qamets puzzles* we have tacitly made the assumption that qamets qatan and gadol are not phonological variants of each other.
# In other words, it never occurs that a qamets gadol becomes shortened into a qamets qatan.
# From the grammar rules it follows that short versions of the qamets can only be
# 
# * patah
# * schwa
# * composite schwa with patah
# 
# and never
# 
# * qamets qatan
# * composite schwa with qamets
# 
# Whether this hypothesis is right, is not my competence. 
# We just use it as a working hypothesis.
# 
# ## Lexical information
# 
# This method is not a pure method, in the sense that it works only with the information given in the source string.
# We *cheat*, i.e. we use morphological information from the ETCBC database to 
# steer us into the right directorion. To this end, the input of the ``phono()`` is always a
# LAF node, from which we can get all information we need.
# 
# More precisely, it is a sequence of nodes.
# This sequence is meant to correspond toa sequence of monads, that is written adjacently
# (no space between, no maqef between).
# From these nodes we can look up:
# 
# * the ETCBC transliteration
# * the qere (if there is a discrepancy between ketiv and qere)
# * additional lexical information (taken from the last node)
# 
# ## Combined words
# 
# You can use ``phono()`` to transliterate multiple words at the same time, but you can also do individual words,
# even if in Hebrew they are written together.
# However, it is better to feed combined words to ``phono()`` in one go, because the prefix word may influence the transliteration of the postfix word. Think of the article followed by word starting with a BGDKPT letter.
# The dagesh in the BGDKPT is interpreted as a lene, if the word stands on its own, but as a forte if it is combined.
# 
# However, it not not advised to feed longer strings to ``phono()``, because when phono retrieves lexical information, it uses the information of the last node that matches a word in the input string.
# 
# ## Accents
# 
# We determine "primary" and "secundary" stress in our transliteration, but this must not be taken in a phonetic sense.
# Every syllable that carries an accent pointing will get a primary stress mark.
# However, a few specific accent pointings are not deemed to produce an an accent, and an other group of accents
# is deemed to produce only a secondary accent.
# The last syllable of a word also gets a secundary accent by default.
# We have not yet tried to be more precise in this, so *segolates* do not get the treatment they deserve.
# 
# The main rationale for accents is that they prevent a qamets to be read as qatan.
# 
# ## Individual symbols
# 
# We have made a careful selection of UNICODE symbols to represent Hebrew sounds.
# Sometimes we follow the phonetic usage of the symbols, sometimes we follow wide spread custom.
# The actual mapping can be plugged in quite easily, 
# and the intermediate stages in the transformation do not use theese final symbols,
# so the algorithm can be easily adapted to other choices.
# 
# ### Consonants
# 
# Provided it is not part of a long vowel, we write yod as ``y``,
# whilst ``j`` would be more in line with the phonetic alphabet.
# 
# Likewise, we write ``ו`` as w, if it is not part of a long vowel.
# 
# With regards to the ``BGDKPT`` letters, it would have been attractive to use the letters ``b g d k p t`` without 
# diacritic for the plosive variants, and with a suitable diacritic for the fricative variants.
# Alas, the UNICODE table does not offer such a suitable diacritic that is available for all these particular 6 letters.
# 
# So, we use ``b g d k p t`` for the plosives, but for the fricatives we use ``v ḡ ḏ ḵ f ṯ``.
# 
# With regards to the *emphatic* consonants ט and ח and צ we represent them with a under dot: ``ṭ ḥ ṣ``.
# ק is just ``q``.
# 
# א and ע translate to translate to ``ʕ`` and ``ʔ``.
# 
# שׁ and שׂ translate to ``š`` and ``ś``.
# ס is just ``s``.
# 
# When א and ה are mater lectionis, they are left out. A ה with mappiq becomes just ``h``,
# like every ה which is not a mater lectionis.
# 
# We do not mark the deviant final forms of the consonants ך and ם and ן and ף and ץ, assuming that
# this is just a scriptural peculiarity, with no effect on the actual sounds.
# 
# The remaining consonants go as follows:
# 
# <table>
# <tr><td>ל</td><td>l</td></tr>
# <tr><td>מ</td><td>m</td></tr>
# <tr><td>נ</td><td>n</td></tr>
# <tr><td>ר</td><td>r</td></tr>
# <tr><td>ז</td><td>z</td></tr>
# </table>
# 
# ### Vowels
# 
# The short vowels (patah, segol, hireq) are just ``a e i`` and qibbuts is just ``u``.
# 
# However, the *furtive* patah is a ``ₐ`` in front of its consonant.
# 
# The long vowels without yod or waw (qamets gadol, tsere, holam) have an over bar ``ā ē ō``.
# 
# The complex vowels (tsere or hireq plus yod, holam plus waw, waw with dagesh) have a circumflex ``ê î ô û``.
# 
# A segol followed by yod becomes ``eʸ``
# 
# The composite schwas (patah, segol, qamets) are written as superscripts ``ᵃ ᵉ ᵒ``.
# 
# The simple schwa is left out if silent, and otherwise it becomes ``ᵊ``.
# 
# ### Accent
# 
# The primary and secundary stress are marked as ``ˈ ˌ`` and are placed *in front of the vowel they occur with*.
# 
# ### Punctuation
# 
# The sof-pasuq ׃ becomes ``.``. 
# If it is followed by ס (setumah) or ף (petuhah) or  ̇׆ (nun-hafuka), these extra symbols are omitted.
# 
# The maqef ־ (between words) becomes ``-``.
# 
# If words are juxtaposed without space in the Hebrew, they are also juxtaposed without space in the phonetic
# transliteration.
# 
# ### Tetragrammaton
# 
# The tetragrammaton is transliterated with the vowels it is encountered with, but the whole is put between 
# square brackets ``[ ]``.
# 
# ### Ketiv-qere
# 
# We base the phonetics on the (vocalized) qere, if a qere is present.
# The ketiv is then ignored. We precede each such word by a ``*`` to indicate that the qere
# is deviant from the ketiv. Using the data view it is possible to see what the ketiv is.The 
# 
# ## Cleaning up
# 
# We leave the accents and the schwas in the end product of the ``phono()`` function,
# despite the fact that the accents, as they appear, do not have consistent phonetic significance.
# And it can be argued that every schwa is silent.
# If you do not care for schwas and accents, it is easy to remove them.
# Also, if you find the results in separating the qamets into qatan and gadol unsatisfying or irrelevant, you can
# just replace them both bij a single symbol, such as ``å``.
# 
# ## Testing
# 
# Quite a bit of code is dedicated to count special cases, to test, and to produce neat tables with interesting forms.
# It is also possible to call the ``phono()`` function in debug mode, which will write to a text file all stages in the
# transliteration from etcbc orginal into the phonetic result.

# # Load the modules

# In[1]:

import sys, os, collections, re
from unicodedata import normalize

from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.lib import Transcription
fabric = LafFabric()


# # Load the LAF data

# In[ ]:

if 'version' not in locals(): version = '4b'
source = 'etcbc'


# In[3]:

API = fabric.load('{}{}'.format(source, version), '--', 'phono', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype label
        g_word_utf8 g_cons_utf8 trailer_utf8
        g_word g_cons lex_utf8 lex
        sp vs vt gn nu ps st
        uvf prs g_prs pfm vbs vbe
        language
        book chapter verse label
    ''',''),
    "prepare": prepare,
}, verbose='NORMAL')
exec(fabric.localnames.format(var='fabric'))
trans = Transcription()


# ## Verse index
# 
# We want to be able to look up the node given a passage and an etcbc transcription string.
# 
# We also want to be able to easily generate a test from an occurrence that we encounter, whether we have the node, or the transcription string with passage.
# For that we need a passage index.

# In[3]:

msg("Compiling passage index")
passage_index = {}
vlab2vnode = {}        # old style verse labels needed for reading ketiv qere data

for bn in F.otype.s('book'):
    book_name = F.book.v(bn)
    for cn in L.d('chapter', bn):
        chapter_num = F.chapter.v(cn)
        for vn in L.d('verse', cn):
            verse_num = F.verse.v(vn)
            passage_index['{} {}:{}'.format(book_name, chapter_num, verse_num)] = vn
            vlab2vnode[F.label.v(vn)] = vn

msg('{} passages (verses)'.format(len(passage_index)))


# ## Load ketiv-qere information

# In[4]:

kq_file = '{}/kq/kq.{}{}'.format(API['data_dir'], source, version)
qeres = {}

info = collections.defaultdict(lambda: [])
not_found = set()
missing = collections.defaultdict(lambda: [])
missed = collections.defaultdict(lambda: [])

error_limit = 10

kq_handle = open(kq_file)

ln = 0
can = 0
cur_label = None

msg("Reading Ketiv-Qere data")
for line in kq_handle:
    ln += 1
    can += 1
    vlab = line[0:10]
    fields = line.rstrip('\n')[10:].split()
    (ketiv, qere) = fields[0:2]
    vnode = vlab2vnode.get(vlab, None)
    if vnode == None:
        not_found.add(vlab)
        continue
    info[vnode].append((ketiv, qere))        
kq_handle.close()
msg("Read {} ketiv-qere annotations".format(ln))

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
    for (ketiv, qere) in info[vnode]:
        wvisited[ketiv] += 1
        windex = wvisited[ketiv]
        ws = wlookup.get(ketiv, None)
        if ws == None or windex > len(ws) - 1:
            missing[vnode].append((windex, ketiv, qere))
            continue
        w = ws[windex]
        qeres[w] = qere
    for ketiv in wlookup:
        if ketiv not in wvisited or len(wlookup[ketiv]) - 1 > wvisited[ketiv]:
            missed[vnode].append((len(wlookup[ketiv]) - (wvisited.get(ketiv, -1) + 1), ketiv))
msg("Parsed {} ketiv-qere annotations".format(len(qeres)))

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


# # The source string

# Here is what we use as our starting point: the etcbc transliteration, with one or two tweaks.
# 
# The ETCBC transcription encodes also what comes after each word until the next word.
# Sometimes we want that extra bit, and sometimes not, and sometimes part of it.

# ## Patterns

# In[5]:

# punctuation
punctuation = re.compile('''
      (?: [ -]\s*\Z)        # space, (no maqef) or nospace
    | (?: 
           0[05]            # sof pasuq or paseq
           (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
           \s*\Z
      )
    | (?:_[SPN]\s*\Z)       #  nun hafukha, setumah, petuhah between words
''', re.X)

split_punctuation = re.compile('''
  (.*?)                 # part before punctuation
  ((?:                  # punctuation itself
      (?: [ &-]\s*)         # space, maqef, or nospace
    | (?: 
           0[05]            # sof pasuq or paseq
           (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
           \s*
      )
    | (?:_[SPN]\s*)         #  nun hafukha, setumah, petuhah between words
  )*)
''', re.X)

start_punct = re.compile('''
      (?: \A[ &-]\s*)       # space, maqef or nospace
    | (?: 
           \A
           0[05]            # sof pasuq or paseq
           (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
           \s*
      )
    | (?:\A\s*_[SPN]\s*)    #  nun hafukha, setumah, petuhah between words
''', re.X)

noorigspace = re.compile('''
      (?: [&-]\Z)           # space, maqef or nospace
    | (?: 
           0[05]            # sof pasuq or paseq
           (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
           \Z
      )
    | (?:_[SPN])+           #  nun hafukha, setumah, petuhah between words
''', re.X)

# setumah and petuhah
# Usually, setumah and petuhah occurr after the end of verse sign.
# In that case we can strip them.
# Sometimes they occur interword. Then we have to replace them by a space
# because the words are otherwise adjacent.
# This operation must be performed before originals are glued together,
# because the _S and _P can only be reliably detected if they are at the end of a word.
# So: set_pet to be used before phono(), in get_orig, but only if get_orig is
# used for phono(). 

set_pet_pattern = re.compile('((?:0[05])?)(_[SNP])+\Z')
tetra_lex = 'JHWH/'

def set_pet_pattern_repl(match):
    (punct, nsp) = match.groups()
    sep = ' § ' if punct == '' and nsp != '' else ''
    return punct+sep


# ## Actions

# In[6]:

def get_orig(w, punct=True, set_pet=False, tetra=True, give_ketiv=False):
    proto = F.g_word.v(w)
    orig =  proto if give_ketiv else qeres.get(w, proto)
    if tetra and F.lex.v(w) == tetra_lex:
        (mat, sep) = split_punctuation.fullmatch(orig).groups()
        orig = '[ '+mat+' ]'+sep
    if not punct:
        orig = punctuation.sub('', orig)
    else:
        if not noorigspace.search(orig):
            orig += ' '
        if not set_pet:
            orig = set_pet_pattern.sub(set_pet_pattern_repl, orig)
    return orig

# find the first occurrence of the string orig in the verse (ETCBC representation)
# Then deliver the sequence of nodes corresponding to that sequence

def find_w(passage, orig, debug=False):
    if len(orig) == 0: return None
    vn = passage_index.get(passage, None)
    if vn == None: return None
    verse_words = L.d('word', vn)
    results = None
    orig = orig.strip()+' '
    lvw = len(verse_words)
    for i in range(lvw):
        target = orig
        for j in range(i, lvw+1):
            target = start_punct.sub('', target)
            if len(target) == 0:
                results = verse_words[i:j]
                break
            if j >= lvw:
                break
            j_orig = get_orig(
                verse_words[j], 
                punct=False, tetra=False, give_ketiv=True,
            ).rstrip('&')
            if target.startswith(j_orig):
                if debug: print('{}-{}: [{}] <= [{}]'.format(i, j, j_orig, target))
                target = target[len(j_orig):]
                if debug: print('{}-{}: [{}]'.format(i, j, target))
                continue
            if debug: print('{}-{}: [{}] <! [{}]'.format(i, j, j_orig, target))
            break
    return results

# partition a list of nodes into chunks 
# whenever a node has an orig string that not ends with an - start a new chunk
def partition_w(wnodes):
    results = []
    cur_chunk = []
    orig = None
    for w in wnodes:
        cur_chunk.append(w)
        orig = get_orig(w, tetra=False)
        if orig.endswith('-'): continue
        results.append(tuple(cur_chunk))
        cur_chunk = []
    if len(cur_chunk):
        results.append(tuple(cur_chunk))
    return results


# # The phonological symbols
# 
# Here is the list of symbols that constitutes the mapping from ETCBC transcription codes to a phonetic transcription.
# It is a series of triplets (*etcbc symbol*, *name*, *phonetic symbol*).
# 
# If changes are needed to the appearance of the phonetic transcriptions (not to its *logic*), here is the place to tweak.
# 
# Note that the order is important.
# In the final stage of the transformation process, these substitutions will be applied in the order they appear here.
# 
# This is especially important for, but not only for, the BGDKPT letters.

# In[7]:

specials = (
    ('>', 'alef', 'ʔ'),
    ('<', 'ayin', 'ʕ'),
    ('v', 'tet', 'ṭ'),
    ('y', 'tsade', 'ṣ'),
    ('x', 'chet', 'ḥ'),
    ('c', 'shin', 'š'),
    ('f', 'sin', 'ś'),
    ('#', 's(h)in', 'ŝ'),

    ('ij', 'long hireq', 'î'),
    ('I', 'short hireq', 'i'),
    (';j', 'long tsere', 'ê'),
    ('ow', 'long holam', 'ô'),
    ('w.', 'long `qibbuts`', 'û'),
    ('ej', 'e glide', 'eʸ'),
    ('j', 'yod', 'y'),

    (':a', 'hataf patach', 'ᵃ'),
    (':@', 'hataf qamats', 'ᵒ'),
    (':e', 'hataf segol', 'ᵉ'),
    ('%', 'schwa mobile', 'ᵊ'),
    (':', 'schwa quiescens', ''),
    ('@', 'qamats gadol', 'ā'),
    ('a', 'patach', 'a'),
    ('`', 'furtive patach', 'ₐ'),
    ('+', 'qamats', 'å'),
    ('e', 'segol', 'e'),
    (';', 'tsere', 'ē',),
    ('i', 'hireq', 'i'),
    ('o', 'holam', 'ō'),
    ('^', 'qamats qatan', 'o'),
    ('u', 'qibbuts', 'u'),

    ('b.', 'b plosive', 'B'),
    ('g.', 'g plosive', 'G'),
    ('d.', 'd plosive', 'D'),
    ('k.', 'k plosive', 'K'),
    ('p.', 'p plosive', 'P'),
    ('t.', 't plosive', 'T'),

    ('b', 'b fricative', 'v'),
    ('g', 'g fricative', 'ḡ'),
    ('d', 'd fricative', 'ḏ'),
    ('k', 'k fricative', 'ḵ'),
    ('p', 'p fricative', 'f'),
    ('t', 't fricative', 'ṯ'),

    ('B', 'b plosive', 'b'),
    ('G', 'g plosive', 'g'),
    ('D', 'd plosive', 'd'),
    ('K', 'k plosive', 'k'),
    ('P', 'p plosive', 'p'),
    ('T', 't plosive', 't'),
    
    ('w', 'waw', 'w'),
    ('l', 'lamed', 'l'),
    ('m', 'mem', 'm'),
    ('n', 'nun', 'n'),
    ('r', 'resh', 'r'),
    ('z', 'zajin', 'z'),
    
    ('!', 'primary accent', 'ˈ'),
    ('/', 'secundary accent', 'ˌ'),
    
    ('&', 'maqef', '-'),
    ('*', 'masora', '*'),
)

specials2 = (
    ('$', 'sof pasuq', '.'),
    ('|', 'paseq', ' '),
    ('§', 'interword setumah and petuhah', ' '),
)


# ## Assembling the symbols in dictionaries
# 
# We compile the table of symbols in handy dictionaries for ease of processing later.
# 
# We need to quickly detect the dagesh lenes later on, so we store them in a dictionary.
# 
# Our treatment of accents is still primitive. 
# 
# We ignore some accents (``irrelevant accents`` below) and we consifer some accents as indicators of a mere
# *secundary* accent (``secundary accents`` below).
# 
# The ``sound_dict`` is the resultig (ordered) mapping of all source characters to "phonetic" characters.

# In[8]:

dagesh_lenes = {'b.', 'g.', 'd.', 'k.', 'p.', 't.'}
dagesh_lene_dict = dict()

irrelevant_accents = (
    ('01', 'segol'),  # occurs always with another accent
    ('03', 'pashta'), # by definition on last syllable: not relevant for accent
    ('04', 'telisha qetana'),
    ('14', 'telisha gedola'),
    ('24', 'telisha qetana'),
    ('44', 'telisha gedola'),
)
secundary_accents = (
    ('71', 'merkha'), # ??
    ('63', 'qadma'),  # ??
    ('73', 'tipeha'), # ??
)
punctuation_accents = (
    ('00', 'sof pasuq'),
    ('05', 'paseq'),
)

known_accents = {x[0] for x in irrelevant_accents+secundary_accents+punctuation_accents}

primary_accents = (
    {'{:>02}'.format(i) for i in range(100) if '{:>02}'.format(i) not in known_accents}
)
sound_dict = collections.OrderedDict() 
sound_dict2 = collections.OrderedDict() 


for (sym, let, glyph) in specials:
    if sym in dagesh_lenes:
        dagesh_lene_dict[sym[0]] = glyph
    else:
        sound_dict[sym] = glyph
        
for (sym, let, glyph) in specials2:
    sound_dict2[sym] = glyph


# # Patterns
# 
# The ``phono()`` function that we will define (far) below, performs an ordered sequence of transformations.
# Most of these are defined as [regular expressions](http://www.regular-expressions.info),
# and some parts of those expressions occur over and over again, e.g. subpatterns for *vowel* and *consonant*.
# 
# Here we define the shortcuts that we are going to use in the regular expressions.
# 
# ## Details of the matching process
# 
# Normally, when a pattern matches a string, the string is consumed: the parts of the pattern that match
# consume corresponding stretches of the string.
# However, in many cases a pattern specifies specific contexts in which a match should be found.
# In those cases we do not want that the context parts of the pattern are responsible for string
# consumption, because in those parts there could be another relevangt match.
# 
# In regular expression there is a solution for that: look-ahead and look-behind assertions and we use them frequently.
# 
# ``(?<=`` *before_pattern* ``)`` *pattern* ``(?=`` *behind-pattern* ``)``
# 
# A match of this pattern in a string is a portion of a string that matches *pattern*, provided that
# portion is preceded by *before_pattern* and followed by *behind* pattern.
# 
# If there is a match, and new matches must be searched for, the search will start right after *pattern*.
# 
# Instead of the above *positive* look-ahead and look-behind assertions, there are also *negative* variants:
# 
# ``(?<!`` *before_pattern* ``)`` *pattern* ``(?!`` *behind-pattern* ``)``
# 
# in those cases the match is good, if the *before_pattern* does not match the preceding material, and analogously
# the *behind_pattern*.
# 
# In Python there is a restriction on look-behind patterns:
# they must be patterns that only have matches of a predictable, fixed length.
# That will make some of our patterns slightly more complicated.
# For example, vowels can be simple or complex, and hence have variable length.
# If we want to specify a consonant, provided it is preceded by a vowel, we have to be careful.
# 
# In regular expressions there are *greedy*, *non-greedy* and *possessive* quantifiers. 
# Greedy ones try to match as many times as possible at first;
# non-greedy ones try to match as few times as possible at first.
# Possessive quantifiers are like greedy ones, but greedy ones will give back occurrences if that helps 
# to achieve a match. Possessive ones do not do that.
# 
# <table>
# <tr><th>kind</th><th>greedy</th><th>non-greedy</th><th>possessive</th></tr>
# <tr><th>0 or more</th><td>``*``</td><td>``*?``</td><td>``*+``</td></tr>
# <tr><th>1 or more</th><td>``+``</td><td>``+?``</td><td>``++``</td></tr>
# <tr><th>at least *n*, at most *m*</th>
#     <td>``{``*n*``,`` *m*``}``</td>
#     <td>``{``*n*``,`` *m*``}?``</td>
#     <td>``{``*n*``,`` *m*``}+``</td>
#  </tr>
# </table>
# 
# For example, the pattern ``[ab]*b`` matches substrings of ``a``s and ``b``s that  in a ``b``.
# In order to match the string ``aaaaab``, the ``[a|b]*`` part starts with greedily consuming the whole string,
# but after discovering that the ``b`` part in the pattern should also match something, the ``[a|b]*`` part
# reluctantly gives back one occurrence. That will do the trick.
# 
# However, ``[ab]*+b`` will not match ``aaaaab``, because the possessive quantifier gives nothing back.
# 
# Possessive quantifiers a desirable in combination with negative look-behind assertions.
# 
# For example, take ``[ab]*+(?!c)$``. This will match substrings of ``a``s and ``b``s that are not followed by ``c``.
# So it matches ``ababab`` but not ``abababc``.
# However, the non-possessive variant, ``[ab]*(?!c)`` matches both. So how does it match ``abababcd``?
# First, the ``[ab]*`` part matches all ``a``s and ``b``s. Then the look-behind assertion that ``c`` does not follow,
# is violated. So ``[ab]*`` backtracks one occurrence, a ``b``. At that point the look-behind assertion finds a ``b`` 
# which is not ``c``, and the match succeeds.
# 
# Python lacks *possessive* quantifiers in regular expressions, so again, this makes some expressions below more complicated than they were otherwise.

# In[9]:

# We want to test for vowels in look-behind conditions.
# Python insists that look-behind conditions match patterns with fixed length.
# Vowels have variable length, so we need to take a bit more context.
# This extra context is dependent on whether the vowel occurs in front of a consonant or after it
# vowel1 is for before, vowel2 is for after, both are usable in look-behind conditions
# vowel matches purely vowels of variable length, and is not usable in look-behind conditions

vowel1 = '(?:(?::[ea@])|(?:w\.)|(?:[i;]j)|(?:ow)|(?:.[%@\^;aeiIou`]))'
vowel2 = '(?:(?::[ea@])|(?:w\.)|(?:[i;]j)|(?:ow)|(?:[%@\^;aeiIou`].))'
vowel = '(?:(?::[ea@])|(?:w\.)|(?:[i;]j)|(?:ow)|(?:[%@\^;aeiIou`]))'

# lvowel are long vowels only (including compositions)
# svowel are short vowels only, including composite schwas
lvowel1 = '(?:(?:w\.)|(?:[i;]j)|(?:ow)|(?:.[@;o]))'
svowel = '(?:(?::[ea@])|(?:[%@\^;aeiIou`]))'

gadol = sound_dict['@']
qatan = sound_dict['^']
a_like = {':a', 'a'}
o_like = {':@', 'o', 'ow', 'u', 'w.'}
e_like = {':', ':e', ';', ';j', 'e', 'i', 'ij'}

# complex i/w vowel: the composite vowels with waw and yod, after translation
complex_i_vowel = ''.join(sound_dict[s] for s in {'ij', ';j'})
complex_w_vowel = ''.join(sound_dict[s] for s in {'ow'})

# consonants
ncons = '[^>bgdhwzxvjklmns<pyqrfct _&$-]' # not a consonant
cons = '[>bgdhwzxvjklmns<pyqrfct]'        # any consonant
consx = '[bgdwzxvjklmns<pyqrfct]'         # any consonant except alef
bgdkpt = '[bgdkpt]'                       # begadkefat consonant
nbgdkpt = '[wzxvjlmns<yqrfc]'             # non-begadkefat consonant
prep = '[bkl]'                            # proclitic preposition

# accents

acc = '[ˈˌ]'                              # primary and secundary accent


# # Regular expressions
# 
# Here are the patterns, but also the replacement functions we are going to carry out when the patterns match.
# How exactly the patterns and replacement functions hang together, is a matter for the phono function itself.

# ## Rafe and furtive patah
# 
# ### Rafe
# 
# The rafe indicates a fricative pronounciation. It cancels a dagesh lene on a BGDKPT letter.
# If it occurs in other situations, we ignore it.
# 
# ### Furtive patah
# 
# We have to reverse any CV pattern at word ends where the V is a patah, and the C is a guttural (i.e. cheth, ayin or he-mappiq).
# 
# If there is an accent on the guttural, we ignore it in these cases, because the guttural does not initiate a syllable.

# In[10]:

# rafe

rafe = re.compile('({b})\.,'.format(b=bgdkpt))

def rafe_repl(match):
    return match.group(1)

# furtive patah
# note that we will deliberately loose any accent on the guttural
furtive_patah = re.compile('([x<]|(?:h\.))(?:[/!]?)a(?=\Z|[ &-])'.format(v1=vowel1))

def furtive_patah_repl(match):
    return '`'+match.group(1)


# ## Accents
# 
# ### Patterns

# In[11]:

# explicit accents

# lets assume that any cantillation mark or accent indicates that the vowel is stressed
# except for some types of mark (qadma, pashta)
sep_accent = re.compile('([0-9]{2})')
remove_accent = re.compile('|'.join('~{}'.format(x[0]) for x in irrelevant_accents))
primary_accent = re.compile('|'.join('~{}'.format(x) for x in primary_accents))
secundary_accent = re.compile('|'.join('~{}'.format(x[0]) for x in secundary_accents))
punctuation_accent = re.compile('({})'.format('|'.join('~{}'.format(x[0]) for x in punctuation_accents)))
condense_accents = re.compile('({v})([!/]+)'.format(v=vowel))

def sep_accent_repl(match):
    return '~'+match.group(1)

def condense_accents_repl(match):
    accent = '!' if '!' in match.group(2) else '/'
    return accent+match.group(1)

# implicit accents
default_accent1 = re.compile('({v}`?{c}?\.?(?:\Z|[ ]))'.format(v=svowel, c=cons))
default_accent2 = re.compile('({v}(?:\Z|[ ]))'.format(v=lvowel1))
strip_accents = re.compile('[0-9*]')

# wrong last accents
last_accent = re.compile('[/!]+(?=[ ]|\Z)')

def default_accent_repl(match):
    return '/'+match.group(1)

def punctuation_accent_repl(match):
    if match.group(1) == '~00': return ' $'
    return ' | '

# separate the phonetic representation from the interword material after it.
# To be used at the end of phono().
# specials2 specify how punctuation (sof pasuq, paseq, interword setumah-petuhah are
# translated).

phono_sep = re.compile('(.*?)([ {}]*)'.format(''.join(x[2] for x in specials2)))
multiple_space = re.compile('  +')

verse_end_phono = re.compile('(\. *)\Z')

def verse_end_phono_repl(match):
    return match.group(1).replace(' ', '')



# ### Actions

# In[12]:

stats = collections.Counter()

def doaccents(orig, debug=False, count=False):
    dout = []

# prepare
    if debug: dout.append(('orig', orig))
    if count: pre = orig
    result = orig.lower().replace('_', ' ')
    if debug: dout.append(('trim', result))
    if count and pre != result: stats['trim'] += 1

# explicit accents
    if count: pre = result
    result = sep_accent.sub(sep_accent_repl, result)
    result = remove_accent.sub('', result)
    result = secundary_accent.sub('/', result)
    result = primary_accent.sub('!', result)
    result = condense_accents.sub(condense_accents_repl, result)
    if debug: dout.append(('accents', result))
    if count and pre != result: stats['accents'] += 1

# punctuation
    if count: pre = result
    result = punctuation_accent.sub(punctuation_accent_repl, result)
    result = strip_accents.sub('', result)
    if debug: dout.append(('punctuation', result))
    if count and pre != result: stats['punctuation'] += 1

# rafe
    if count: pre = result
    result = rafe.sub(rafe_repl, result)
    result = result.replace(',', '')
    if debug: dout.append(('rafe', result))
    if count and pre != result: stats['rafe'] += 1

# furtive patah
    if count: pre = result
    result = furtive_patah.sub(furtive_patah_repl, result)    
    if debug: dout.append(('furtive_patah', result))
    if count and pre != result: stats['furtive_patah'] += 1

# implicit accents
    if count: pre = result
    if '!' not in result and '/' not in result:    
        result = default_accent1.sub(default_accent_repl, result)
        if not '/' in result:
            result = default_accent2.sub(default_accent_repl, result)
    result = last_accent.sub('', result)
    if debug: dout.append(('default accent', result))
    if count and pre != result: stats['default_accent'] += 1

# deliver
    return (result, dout) if debug else result


# ## Qamets gadol and qatan
# 
# ### Patterns

# In[13]:

# qamets qatan  
# NB: all patterns stipulate that the qamets (@) in question is unaccented

 # near end of word:
qamets_qatan1 = re.compile('(?<={c})(\.?)@(?={c}(?:\.?[/!]?(?:[ &-]|\Z)))'.format(c=consx))

# before dagesh forte:
qamets_qatan2 = re.compile('(?<={c})(\.?)@(?={c}\.)'.format(c=cons))

# if the following consonant is BGDKFT and does not have dagesh, the @ is in an open syllable:
qamets_qatan3 = re.compile('(?<={c})(\.?)@(?={c}:(?:{nb}|(?:{b}\.)))'.format(c=cons, b=bgdkpt, nb=nbgdkpt))

# assimilation of qamets with following composite schwa of type (chatef qamets),
#     but if the qamets is under a preposition BCL, not if it is under the article H:
qamets_qatan4a = re.compile('(?<={p})(\.?[!/]?)@(?=-{c}:@)'.format(p=prep, c=cons))

#     or word-internal
qamets_qatan4b = re.compile('(?<={c})(\.?[!/]?)@(?={c}:@)'.format(c=cons))

# before an other qamets qatan, provided the syllable is unaccented
qamets_qatan5 = re.compile('(?<={c})(\.?)@(?={c}\.?[/!]?\^)'.format(c=cons))

# in a pronominal suffix, qamets never becomes qatan.
# This pattern will be applied only on words that do have a non-empty pronominal suffix
# The pattern will spot the qamets qatan in front of the last consonant, if there is such a qatan

qamets_qatan_prs = re.compile('\^(?=[0-9]*{c}\.?[/!]?(?:[ &-]|\Z))'.format(c=cons))

def qamets_qatan_repl(match):
    return match.group(1)+'^'

# there are exceptions to the heuristic of interpreting qamets by voting between occurrences
qamets_qatan_x = '''
BJT/ => 1A
JM/ => 1O
JWMM => 2A
JRB<M/ => 1A
JHWNTN/ => 2A
'''

xxx = '''
<YBT/ => 2A
'''

# there are unaccented conjugated verb forms that must not be subjected to qamets-qatan transformation
qamets_qatan_verb_x = {
    'verb qal perf 3sf',
    'verb qal perf 3p-',
    'verb nif impf 1s-',
    'verb nif impf 1p-',
    'verb nif impf 2sf',
    'verb nif impf 2pm',
    'verb nif impf 3pm',
    'verb nif impv 2sf',
    'verb nif impv 2pm',
}
qqv_experimental = {
    'verb qal impf 3pm',
}

qamets_qatan_verb_x |= qqv_experimental

def qamets_qatan_verb_x_repl(match):
    return match.group(1)+'@'
# for the use of applying individual corrections:


# ### Actions
# Here is the function that carries out rule based qamets qatan detection, without going into
# verb paradigms and exceptions. It is the first go at it.

# In[14]:

def doplainqamets(word, accentless=False, debug=False, count=False):
    dout = []
    result = word
    if accentless:
        result = result.replace('!', '').replace('/', '')
    if count: pre = result
    result = qamets_qatan1.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan1', result))
    if count and pre != result: stats['qamets_qatan1'] += 1

    if count: pre = result
    result = qamets_qatan2.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan2', result))
    if count and pre != result: stats['qamets_qatan2'] += 1

    if count: pre = result
    result = qamets_qatan3.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan3', result))
    if count and pre != result: stats['qamets_qatan3'] += 1

    if count: pre = result
    result = qamets_qatan4a.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan4a', result))
    if count and pre != result: stats['qamets_qatan4a'] += 1

    if count: pre = result
    result = qamets_qatan4b.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan4b', result))
    if count and pre != result: stats['qamets_qatan4b'] += 1

    return (result, dout) if debug else result


# ## Schwa and dagesh
# 
# ### Schwa
# 
# The rules for the schwa that I have found are contradictory.
# 
# These rules I have seen (e.g.) 
# 
# 1. if two consecutive consonants have both a schwa, the second one is mobile;
# 1. a schwa under a consonant with dagesh forte is mobile
# 1. a schwa under the last consonant of a word is quiescens
# 1. a schwa on a consonant that follows a long vowel, is mobile
# 
# But there are examples that rules 1 and 3 apply at the same time.
# 
# And in the qal 3 sg f forms end with a tav with schwa, often preceded by a consonant with also schwa.
# In this case the tav has a dagesh, which by the rules for dagesh cannot be a lene. So it must be a forte.
# So this violates rule 2.
# 
# We will cut this matter short, and make any final schwa quiescens.
# 
# As to rule 4, there are cases where the schwa in question is also followed by a final consonant with schwa.
# In those cases it seems that the schwa in question is silent.

# In[15]:

# mobile schwa
mobile_schwa1 = re.compile('''
    (                           # here is what goes before the schwa in question
        (?:(?:\A|[ &-]).\.?)|   # an initial consonant or
        (?:.\.)|                # a consonant with dagesh (which must be forte then) or 
        (?::.\.?)|              # another schwa and then a consonant
        (?:                     # a long vowel such as the following
            (?:
                @>?|               # qamets possibly with alef as mater lectionis (the remaining qametses are gadol)
                ;j?|               # tsere, possibly followed by yod
                ij|                # hireq with yod
                o[>w]?|            # holam possibly followed by yod
                w\.                # waw with dagesh
            )
            {c}                 # and then a consonant
        )
    )
    :
    (?![@ae])                   # the schwa may not be composite
'''.format(c=cons), re.X)

mobile_schwa2 = re.compile(':(?={b}(?:[^.]|[ &-]|\Z))'.format(b=bgdkpt)) # before BGDKPT letter without dagesh

# second last consonant with schwa when last consonsoant also has schwa
mobile_schwa3 = re.compile('[%:](?={c}\.?{a}?[%:](?:[ &]|\Z))'.format(a=acc, c=cons))

# all schwas and the end of the word are quiescens, only if the words are not glued together
mobile_schwa4 = re.compile('[%:](?=[ &]|\Z)')

def mobile_schwa1_repl(match):
    return match.group(1)+'%'

# dagesh
dages_forte_lene = re.compile('(?<={v1})(-*)({b})\.(?=[/!]?{v2})'.format(v1=vowel1, v2=vowel, b=bgdkpt))
dages_forte = re.compile('(?<={v1})(-?[h>]*-*)([^h])\.(?=[/!]?{v2})'.format(v1=vowel1, v2=vowel))
dages_lene = re.compile('({b})\.'.format(b=bgdkpt))

def dages_forte_lene_repl(match):
    return match.group(1)+(dagesh_lene_dict[match.group(2)] * 2)

def dages_lene_repl(match):
    return dagesh_lene_dict[match.group(1)]

def dages_forte_repl(match):
    return match.group(1) + match.group(2) * 2


# ## Mater lectionis and final fixes

# In[16]:

# silent aleph
silent_aleph = re.compile('(?<=[^ &-])>(?!(?:[/!]|{v}))'.format(v=vowel))

# final mater lectionis
# I assume that heh and alef are only matrices lectionis after a LONG vowel
last_ml = re.compile('(?<={v1})[>h]+(?=[ &-]|\Z)'.format(v1=lvowel1))
last_ml_jw = re.compile('jw(?=[ &-]|\Z)')

# mappiq heh
mappiq_heh = re.compile('h\.')

fixit_i = re.compile('([{v}])\.'.format(v=complex_i_vowel))
fixit_w = re.compile('([{v}])\.'.format(v=complex_w_vowel))
fixit = re.compile('(.)\.')

split_sep = re.compile('^(.*?)([ .&$\n-]*)$') # to split the result in the phono part and the interword part

def fixit_repl(match):
    return match.group(1) * 2

def fixit_i_repl(match):
    return match.group(1)+'j'

def fixit_w_repl(match):
    return match.group(1)+'w'

# END OF REGULAR EXPRESSIONS AND REPLACEMENT FUNCTIONS


# ## Qamets corrections
# 
# For some words we need specific corrections.
# The rules for qamets qatan are not specific enough.
# 
# ### Correction mechanism
# 
# We define a function ``apply_corr(wordq, corr)`` that can apply a correction instruction to ``wordq``, which is a word in pre-transliterated form, i.e. a word that has underwent transliteration steps ending with qamets interpretation, including applying special verb cases.
# 
# The ``corr`` is a comma-separated list of basic instructions, which have the form
# *number* *letter*. It will interpret the *number*-th qamets as a gadol of qatan, depending on whether *letter* = ``ā`` or ``o``.
# 
# ### Precomputed list of corrections
# 
# Later on we compile a dictionary ``qamets_corrections`` of pre-computed corrections.
# This dictionary is keyed by the pre-transliterated form, and valued by the corresponding correction string. Here we initialize this dictionary.
# 
# The ``phono()`` function that carries out the complete transliteration, looks by default in ``qamets_corrections``, but this can be overridden. These corrections will not be carried out for the special verb cases.

# In[17]:

qamets_corrections = {} # list of translits that must be corrected

# apply correction instructions to a word

def apply_corr(wordq, corr):
    if corr == '': return wordq
    corrs = corr.split(',')
    indices=[]
    for (i, ch) in enumerate(wordq):
        if ch == '^' or (ch == '@' and (i == 0 or wordq[i-1] != ':')):
            indices.append(i)
    resultlist = list(wordq)
    for c in corrs:
        (pos, kind) = c
        pos = int(pos) - 1
        repl = '^' if kind == 'o' else '@'
        if pos >= len(indices):
            msg('Line {}: pos={} out of range {}'.format(ln, pos, indices))
            continue
        rpos = indices[pos]
        resultlist[rpos] = repl
    return''.join(resultlist)


# ### Feature value normalization
# 
# We need concise, normalized values for the lexical features.

# In[18]:

undefs = {'NA', 'unknown', 'n/a', 'absent'}

png = dict(
    NA='-',
    unknown='-',
    p1='1',
    p2='2',
    p3='3',
    sg='s',
    du='d',
    pl='p',
    m='m',
    f='f',
    a='a',
    c='c',
    e='e',
)
png['n/a'] = '-'


# ### Lexical info
# 
# We need a label for lexical information such as part of speech, person, number, gender.

# In[19]:

declensed = {'subs', 'nmpr', 'adjv', 'prps', 'prde', 'prin'}

def get_lex_info(w):
    sp = F.sp.v(w)
    lex_infos = [sp]
    if sp == 'verb':
        lex_infos.extend([F.vs.v(w), F.vt.v(w), '{}{}{}'.format(png[F.ps.v(w)], png[F.nu.v(w)], png[F.gn.v(w)])])
    elif sp in declensed:
        lex_infos.append('{}{}'.format(png[F.nu.v(w)], png[F.gn.v(w)]))
    lex_info = ' '.join(lex_infos)
    if sp == 'verb' or sp in declensed:
        prs = F.g_prs.v(w)
        if prs not in undefs:
            lex_info += ',{}'.format(prs.lower())
    return lex_info

def get_decl(lex_info):
    if lex_info == None: lex_info = ''
    parts = lex_info.split(',')
    return lex_info if len(parts) == 1 else parts[0]

def get_prs(lex_info):
    if lex_info == None: lex_info = ''
    parts = lex_info.split(',')
    return '' if len(parts) == 1 else parts[1]


# # The phono function
# 
# The definition of the function that generates the phonological transliteration.
# It is a function with a big definition, so we have broken it in parts.
# 
# ## Phono parts

# In[20]:

interesting_stats = [
    'total',
    'qamets_verb_suppress_qatan',
    'qamets_prs_suppress_qatan',
    'qamets_qatan_corrections',
]


# In[21]:

# if suppress_in_verb, phono will suppress qatan interpretation in certain verb paradigmatic forms
# if suppress_in_prs, phono will suppress qatan interpreation in pronominal suffixes
# if correct is 1, phono will apply individual corrections
# if correct is 0, phono will not apply individual corrections
# if correct is -1, phono will stop just before applying the qamets qatan corrections and return
# the intermediate result

def phono_qamets(
        ws, result, lex_info,
        debug, count, dout,    
        suppress_in_verb, suppress_in_prs,
        correct, corrections, 
    ):
# qamets qatan

# check whether we are in a verb paradigm that requires suppressing qamets => qatan
    if count: pre = result
    suppr = True
    decl = get_decl(lex_info)

    if suppress_in_verb:
        suppr = False
        if decl == '':
            if debug: dout.append(('qamets qatan', 'no special verb form invoked'))
        elif decl not in qamets_qatan_verb_x:
            if debug: dout.append(('qamets qatan', 'no special verb form: {}'.format(decl)))
        elif '@' not in result:
            if debug: dout.append(('qamets qatan', 'special verb form: no qamets present'))
        elif '!' in result:
            if debug: dout.append(('qamets qatan', 'special verb form: primary accent present'))
            suppr = True
        else:
            suppr = True
            if count: stats['qamets_verb_suppress_qatan'] += 1
    else:
        if debug: dout.append(('qamets qatan', 'suppression for verb forms is switched off'))
        suppr = False
    
    if suppr:
        if debug: dout.append(('qamets qatan', 'special verb form: qatan suppressed for {}'.format(decl)))
    else:
        if debug:
            (result, this_dout) = doplainqamets(result, debug=True, count=count)
            dout.extend(this_dout)
        else: result = doplainqamets(result, count=count)

# check whether we have a pronominal suffix that requires suppressing qamets => qatan

    if count: pre = result
    suppr = True
    prs = get_prs(lex_info)
    if suppress_in_prs:
        suppr = False
        if prs == '':
            if debug: dout.append(('qamets qatan', 'no pron suffix indicated'))
        elif '@' not in prs:
            if debug: dout.append(('qamets qatan', 'pronominal suffix: no qamets present'))
        elif not qamets_qatan_prs.search(result):
            if debug: dout.append(('qamets qatan', 'pron suffix {}: no qamets qatan present'.format(prs)))
        else:
            suppr = True
            if count: stats['qamets_prs_suppress_qatan'] += 1
    else:
        if debug: dout.append(('qamets qatan', 'suppression for pron suffix is switched off'))
        suppr = False
    
    if suppr:
        result = qamets_qatan_prs.sub('@', result)
        if debug:
            dout.append(('qamets qatan', 'pron suffix {}: qatan suppressed'.format(prs)))
            dout.append(('qamets qatan prs', result))

# now change gadol in qatan in front of other qatan
    if count: pre = result
    result = qamets_qatan5.sub(qamets_qatan_repl, result)
    if debug: dout.append(('qamets_qatan5', result))
    if count and pre != result: stats['qamets_qatan5'] += 1

# handle desired corrections
    if count: pre = result
    if correct == -1: return (result, True)
    if correct == 1 and decl not in qamets_qatan_verb_x:
        if corrections == None: corrections = qamets_corrections
        parts = result.split('-')
        hotpart = parts[-1]
        wordq = phono(ws[-1], correct=-1, punct=False)
        if wordq in corrections:
            hotpartn = apply_corr(hotpart, corrections[wordq])
            if debug: dout.append((
                'qamets qatan',
                'correction: {} => {}'.format(hotpart, hotpartn)
            ))
            parts[-1] = hotpartn
            result = '-'.join(parts)
    if debug: dout.append(('qamets_qatan_corr', result))
    if count and pre != result: stats['qamets_qatan_corrections'] += 1

    return (result, False)


# In[22]:

def phono_patterns(result, debug, count, dout):
    
# mobile schwa
    if count: pre = result
    result = mobile_schwa1.sub(mobile_schwa1_repl, result)
    if debug: dout.append(('mobile_schwa1', result))
    if count and pre != result: stats['mobile_schwa1'] += 1

    if count: pre = result
    result = mobile_schwa2.sub('%', result)
    if debug: dout.append(('mobile_schwa2', result))
    if count and pre != result: stats['mobile_schwa2'] += 1

    if count: pre = result
    result = mobile_schwa3.sub('', result)
    if debug: dout.append(('mobile_schwa3', result))
    if count and pre != result: stats['mobile_schwa3'] += 1

    if count: pre = result
    result = mobile_schwa4.sub('', result)
    if debug: dout.append(('mobile_schwa4', result))
    if count and pre != result: stats['mobile_schwa4'] += 1

# dagesh
    if count: pre = result
    result = dages_forte_lene.sub(dages_forte_lene_repl, result)    
    if debug: dout.append(('dagesh_forte_lene', result))
    if count and pre != result: stats['dagesh_forte_lene'] += 1

    if count: pre = result
    result = result.replace('ij.', 'Ijj')
    result = dages_forte.sub(dages_forte_repl, result)
    if debug: dout.append(('dagesh_forte', result))
    if count and pre != result: stats['dagesh_forte'] += 1

    if count: pre = result
    result = dages_lene.sub(dages_lene_repl, result)
    if debug: dout.append(('dagesh_lene', result))
    if count and pre != result: stats['dagesh_lene'] += 1

# silent aleph (but not in tetra)
    if count: pre = result
    if '[' not in result:
        result = silent_aleph.sub('', result)    
    if debug: dout.append(('silent_aleph', result))
    if count and pre != result: stats['silent_aleph'] += 1

# final mater lectionis (but not in tetra)
    if count: pre = result
    if '[' not in result:
        result = last_ml_jw.sub('ʸw', result)
        result = last_ml.sub('', result)    
    if debug: dout.append(('last_ml', result))
    if count and pre != result: stats['last_ml'] += 1

# mappiq heh
    if count: pre = result
    result = mappiq_heh.sub('h', result)
    if debug: dout.append(('mappiq_heh', result))
    if count and pre != result: stats['mappiq_heh'] += 1

    return result


# In[23]:

def phono_symbols(ws, result, debug, count, dout):

# split the result in parts corresponding with the word nodes of the original
    resultparts = result.split('-')
    results = []
    for (i, w) in enumerate(ws):
        resultp = resultparts[i]
        result = resultp
        # masora
        if w in qeres: result = '*'+result

        for (sym, repl) in sound_dict.items():
            result = result.replace(sym, repl)
        if debug: dout.append(('symbols', result))

        # fix left over dagesh and mappiq
        if count: pre = result
        result = fixit_i.sub(fixit_i_repl, result)
        if debug: dout.append(('fixit_i', result))
        if count and pre != result: stats['fixit_i'] += 1

        if count: pre = result
        result = fixit_w.sub(fixit_w_repl, result)
        if debug: dout.append(('fixit_w', result))
        if count and pre != result: stats['fixit_w'] += 1

        if count: pre = result
        result = fixit.sub(fixit_repl, result)
        if count and pre != result: stats['fixit'] += 1
        if debug: dout.append(('fixit', result))

        if count: pre = result
        for (sym, repl) in sound_dict2.items():
            result = result.replace(sym, repl)
        if debug: dout.append(('punct', result))
        if count and pre != result: stats['punct'] += 1

    # zero width word boundary
        if count: pre = result
        result = multiple_space.sub(' ', result)
        result = result.replace('[ ', '[').replace(' ]', ']') #tetra
        if debug: dout.append(('cleanup', result))
        if count and pre != result: stats['cleanup'] += 1
        results.append(result)

    return results


# ## Phono whole
# Here the rule fabrics are woven together, exceptions invoked.

# In[24]:

def phono(
        ws, 
        suppress_in_verb=True, suppress_in_prs=True,
        correct=1, corrections=None, 
        inparts=False,
        debug=False,
        count=False,
        punct=True,
    ):
    if type(ws) is int: ws = [ws]
    if count: stats['total'] += 1
    dout = []
# collect information
    orig = ''.join(get_orig(w, punct=True) for w in ws)
    lex_info = get_lex_info(ws[-1])
# strip punctuation at the end, if needed
    if not punct: orig = punctuation.sub('', orig)
# account for ketiv-qere if in debug mode
    if debug:
        for w in ws:
            if w in qeres:
                dout.append(('ketiv-qere', '{} => {}'.format(F.g_word.v(w), qeres[w])))
# accents
    if debug: (result, dout) = doaccents(orig, debug=True, count=count)
    else: result = doaccents(orig, count=count)
# qamets        
    (result, deliver) = phono_qamets(
        ws, result, lex_info,
        debug, count, dout,    
        suppress_in_verb, suppress_in_prs,
        correct, corrections, 
    )
    if deliver: return (result, dout) if debug else result
# patterns
    result = phono_patterns(result, debug, count, dout)
# symbols
    results = phono_symbols(ws, result, debug, count, dout)
    result = ''.join(results) if not inparts else results
# deliver
    return (result, dout) if debug else result


# # Skeleton analysis
# 
# We have to do more work for the qamets. Sometimes a word form on its own is not enough to determine whether a qamets is gadol or qatan. In those cases, we analyse all occurrences of the same lexeme, and for each syllable position we measure whether an A-like vowel of an O-like vowel tends to occur in that syllable.
# 
# In order to do that, we need to compute a *vowel skeleton* for each word.

# ## Stripping paradigmatic material
# 
# A word may have extra syllables, due to inflections, such as plurals, feminine forms, or suffixes. Let us call this the *paradigmatic material* of a word. 
# 
# Now, we strip from the initial vowel skeleton a number of trailing vowels that corresponds
# to the number of consonants found in the paradigmatic material.
# This is rather crude, but it will do.

# In[25]:

# we need the number of letters in a defined value of a morpho feature
def len_suffix(v):
    if v == None: return 0
    if v in undefs: return 0
    return len(v.replace('=', '').replace('W', '').replace('J', ''))

# we need a function that return 1 for plural/dual subs/adj and for fem adj
def len_ending(sp, n, g):
    if sp == 'subs': return 1 if n in {'pl', 'du'} else 0
    if sp == 'adjv': return 1 if n in {'pl', 'du'} or g in 'f' else 0 
    return 0

# return the number of consonants in the suffixes
def len_morpho(w):
    return max((
        len_suffix(F.prs.v(w)) + len_suffix(F.uvf.v(w)), 
        len_ending(F.sp.v(w), F.nu.v(w), F.gn.v(w)),
    ))


# ## Skeleton patterns
# 
# Next, we reduce the vowel skeleton to a skeleton pattern. We are not interested in all vowels, only in whether the vowel is a qamets (gadol or qatan), A-like, O-like, or other (which we dub E-like).

# In[26]:

# the qamets gadol/qatan skeleton
qamets_qatan_skel = re.compile('([^@^])')

# the vowel skeleton where the qamets gadol/qatan are preserved as @ and ^
# another o-like vowel becomes O (holam, qamets chatuf) (no waws nor yods)
# another a-like vowel becomes A (patah, patah chatuf) (no alefs)
silent_alef_start = re.compile('([ &-]|\A)>([!/]?(?:[^!/.:;@^aeiou]|\Z))')

def silent_alef_start_repl(match):
    return match.group(1)+'E'+match.group(2)

qamets_qatan_fullskel = re.compile('''
    (
        E                                         # replacement of silent initial alef without vowels
    |   (?::[@ae]?)                                # a (composite) schwa
    |   (?:[;i]j) | (?:ow) | (?:w.)               # a composite vowel   
    |   [@a;eiou^]                                # a vowel point
    |   .                                         # anything else
    )
'''.format(c=cons), re.X)

def qamets_qatan_fullskel_repl(match):
    found = match.group(1)
    if found == 'E': return 'E'
    if found == '@': return gadol
    if found == '^': return qatan
    if found in a_like: return 'A'
    if found in o_like: return 'O'
    if found in e_like: return 'E'
    return ''

def get_full_skel(w, debug=False):
    wordq = phono(w, correct=-1, punct=False)
    wordqr = silent_alef_start.sub(silent_alef_start_repl, wordq)
    fullskel = qamets_qatan_fullskel.sub(qamets_qatan_fullskel_repl, wordqr)
    ending_length = len_morpho(w)
    relevant_part = len(fullskel) - ending_length
    if debug: print('{}: {} => {} => {} : {} minus {} = {}'.format(
        w, orig, wordq, wordqr, fullskel, ending_length, fullskel[0:relevant_part],
    ))

    return fullskel[0:relevant_part]


# # Qamets gadol qatan: sophisticated
# 
# A lot of work is needed to get the qamets gadol-qatan right.
# This involves looking at accents, verb paradigms and special cases among the non-verbs.

# ## Qamets gadol qatan: non-verbs
# 
# Sometimes a qamets is gadol or qatan for lexical reasons, i.e. it can not be derived by rules based on the word occurrence itself, but other occurrences have to be invoked.
# 
# ### All candidates

# In[27]:

# find lexemes which have an occurrence with a qamets (except verbs)
msg("Looking for non-verb qamets")
qq_words = set()
qq_lex = collections.defaultdict(lambda: [])

for w in F.otype.s('word'):
    ln = F.language.v(w)
    if ln != 'Hebrew': continue
    sp = F.sp.v(w)
    if sp == 'verb': continue
    orig = get_orig(w, punct=False, tetra=False)
    if '@' not in orig: continue   # no qamets in word
    word = doaccents(orig)
    lex = F.lex.v(w)
    if word in qq_words: continue
    qq_words.add(word)
    qq_lex[lex].append(w)
msg('{} lexemes and {} unique occurrences'.format(len(qq_lex), len(qq_words)))


# ### Filtering interesting candidates

# In[28]:

msg('Filtering lexemes with varied occurrences')
qq_varied = collections.defaultdict(lambda: [])
nocc = 0
for lex in qq_lex:
    ws = qq_lex[lex]
    if len(ws) == 1: continue
    occs = []
    skel_set = set()
    has_qatan = False
    has_gadol = False
    for w in ws:
        wordq = phono(w, correct=-1, punct=False)
        skel = qamets_qatan_skel.sub('', wordq.replace(':@','')).replace('@',gadol).replace('^',qatan)
        if gadol in skel: has_gadol = True
        if qatan in skel: has_qatan = True
        skel_set.add(skel)
        occs.append((skel, w))
    if len(skel_set) > 1 and has_qatan and has_gadol:
        for (skel, w) in occs:
            fullskel = get_full_skel(w)
            qq_varied[lex].append((skel, fullskel, w))
            nocc += 1
msg('{} interesting lexemes with {} unique occurrences'.format(len(qq_varied), nocc))


# ### Guess the qamets

# In[29]:

qamets_qatan_xc = dict(
    (x[0], x[1]) for x in (y.split(' => ') for y in qamets_qatan_x.strip().split('\n'))
)
qamets_qatan_xcompiled = collections.defaultdict(lambda: {})
for (lex, corrstr) in qamets_qatan_xc.items():
    corrs = corrstr.split(',')
    for corr in corrs:
        (pos, ins) = corr
        pos = int(pos) - 1
        qamets_qatan_xcompiled[lex][pos] = ins

def compile_occs(lex, occs):
    vowel_counts = collections.defaultdict(lambda: collections.Counter())
    for (skel, fullskel, w) in occs:
        for (i, c) in enumerate(fullskel):
            vowel_counts[i][c] += 1
    occs_compiled = {}
    for i in sorted(vowel_counts):
        vowel_count = vowel_counts[i]
        a_ish = vowel_count.get(gadol, 0) + vowel_count.get('A', 0)
        o_ish = vowel_count.get(qatan, 0) + vowel_count.get('O', 0)
        if a_ish != o_ish: occs_compiled[i] = gadol if a_ish > o_ish else qatan
    if lex in qamets_qatan_xcompiled:
        override = qamets_qatan_xcompiled[lex]
        for i in override:
            ins = override[i]
            old_ins = occs_compiled.get(i, '')
            new_ins = gadol if ins == 'A' else qatan
            if old_ins == new_ins:
                print('{}: No override needed for syllable {} which is {}'.format(
                    lex, i+1, old_ins,
                ))
            else:
                print('{}: Override for syllable {}: {} becomes {}'.format(
                    lex, i+1, old_ins, new_ins,
                ))
                occs_compiled[i] = new_ins
    return occs_compiled

def guess_qq(occ, occs_compiled, debug=False):
    (skel, fullskel, w) = occ
    guess = ''
    for (i, c) in enumerate(fullskel):
        guess += occs_compiled.get(i, c) if c == gadol or c == qatan else c
    if debug: print('{}'.format(w))
    return guess

def get_corr(fullskel, guess, debug=False):
    n = 0
    corr = []
    for (i, fc) in enumerate(fullskel):
        if fc != qatan and fc != gadol: continue
        n += 1
        gc = guess[i]
        if fc == gc: continue
        corr.append('{}{}'.format(n, gc))
    if debug: print('{} guess {} corr {}'.format(fullskel, guess, corr))
    return ','.join(corr)


# ### Carrying out the guess work

# In[30]:

msg('Guessing between gadol and qatan')
qamets_corrections = {}
qq_varied_remaining = set()
ndiff_occs = 0
ndiff_lexs = 0
nconflicts = 0
for lex in qq_varied:
    debug = False
    occs = qq_varied[lex]
    occs_compiled = compile_occs(lex, occs)
    this_ndiff_occs = 0
    for occ in occs:
        (skel, fullskel, w) = occ
        guess = guess_qq(occ, occs_compiled, debug=debug)
        corr = get_corr(fullskel, guess, debug=debug)
        if corr:
            this_ndiff_occs += 1
            wordq = phono(w, correct=-1, punct=False)
            if wordq in qamets_corrections:
                old_corr = qamets_corrections[wordq]
                if old_corr != corr:
                    print('Conflicting corrections for {} {} {} ({} => {}): first {} and then {}'.format(
                        lex, wordq, skel, fullskel, guess, old_corr, corr,
                    ))
                    nconflicts += 1
            qamets_corrections[wordq] = corr

    if this_ndiff_occs:
        ndiff_lexs += 1
        ndiff_occs += this_ndiff_occs
        qq_varied_remaining.add(lex)
msg('{} lexemes with modified occurrences ({})'.format(ndiff_lexs, ndiff_occs))
msg('{} patterns with conflicts'.format(nconflicts))


# # Testing
# 
# The function below reads a text file with tests.
# 
# A test is a tab separated line with as fields:
# 
#     passage etcbc-original phono_transcription expected_result bol_reference comments
#     
# The testing routine executes all tests, checks the results, produces onscreen output, debug output in file, and pretty output in a html file.

# ## Auxiliary functions
# 
# ### Composing tests
# 
# Given an occurrence in etcbc translit in a passage, or a node number, we want to easily compile a test out of it.
# Say we are looking for ``orig``.
# 
# The match need not be perfect. 
# We want to find the node w, which carries a translit that occurs at the end of ``orig``.
# If there are multiple, we want the longest.
# If there are multiple longest ones, we want the first that occurs in the passage.

# In[31]:

def get_hebrew(orig):
    origm = Transcription.suffix_and_finales(orig)
    return Transcription.to_hebrew(origm[0]+origm[1]).replace('-','')

def get_passage(w):
    vn = w if F.otype.v(w) == 'verse' else L.u('verse', w)
    return '{} {}:{}'.format(
        F.book.v(L.u('book', w)),
        F.chapter.v(L.u('chapter', w)),
        F.verse.v(vn),
    )

def maketest(ws=None, orig=None, passage=None, expected=None, comment=None):
    if comment == None: comment = 'isolated case'
    if ws == None:
        if passage != None and orig != None: ws = find_w(passage, orig)
    if ws == None:
        print('Cannot make test: {}: {} not found'.format(passage, orig))
        return None
    else:
        if type(ws) is int: ws = [ws]
        passage = get_passage(ws[-1])            
        if expected == None: expected = phono(ws, punct=False)
        test = (ws, expected.rstrip(' '), comment)
    return test


# ### Formatting test results
# 
# Here are some HTML/CSS definitions for pretty printing test results.

# In[32]:

def h_esc(txt):
    return txt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def test_html_head(title, stats, mystats): 
    return '''<html>
<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=UTF-8" />
    <title>'''+title+'''</title>
    <style type="text/css">
        .h {
            font-family: Ezra SIL, SBL Hebrew, Verdana, sans-serif; 
            font-size: x-large;
            text-align: right;
        }
        .t {
            font-family: Menlo, Courier New, Courier, monospace;
            font-size: small;
            color: #0000cc;        
        }
        .tl {
            font-family: Menlo, Courier New, Courier, monospace;
            font-size: medium;
            font-weight: bold;
            color: #000000;        
        }
        .p {
            font-family: Verdana, Arial, sans-serif;
            font-size: medium;
        }
        .l {
            font-family: Verdana, Arial, sans-serif;
            font-size: small;
            color: #440088;
        }
        .v {
            font-family: Verdana, Arial, sans-serif; 
            font-size: x-small;
            color: #666666;
        }
        .c {
            font-family: Ezra SIL, SBL Hebrew, Verdana, sans-serif;
            font-size: small;
            background-color: #ffffdd;
            width: 20%;
        }
        .cor {
            font-family: Menlo, Courier New, Courier, monospace;
            font-weight: bold
            font-size: medium;
        }
        .exact {
            background-color: #88ffff;
        }
        .good {
            background-color: #88ff88;
        }
        .error {
            background-color: #ff8888;
        }
        .norm {
            background-color: #8888ff;
        }
        .ca {
            background-color: #88ffff;
        }
        .cr {
            background-color: #ffff33;
        }
    </style>
</head><body>
'''+(('<p>'+stats+'</p>') if stats else '')+(('<p>'+mystats+'</p>') if mystats else '')+'''
<table>
'''

test_html_tail = '''</table>
</body>
</html>
'''


# ### Run tests
# 
# This is the function that runs a sequence of tests.
# If the second argument is a string, it reads a tab separated file with tests from a file with that name.
# Otherwise it should be a list of tests, a test being a list or tuple consisting of:
# 
#     source, orig, lex_info, expected, comment
#     
# where ``source`` is either a string ``passage`` or a number ``w``.
# If it is a ``w``, it is the node corresponding to the word, and it is used to get the ``passage, orig, lex_info`` which are allowed to be empty.
# If it is a ``passage``, the node will be looked up on the basis of it plus ``orig``.
# If the node is found, it will be used to get the ``lex_info``, if not, the given ``lex_info`` will be used.

# In[33]:

def vfname(inpath):
    (indir, infile) = os.path.split(inpath)
    (inbase, inext) = os.path.splitext(infile)
    return os.path.join(indir, inbase+version+inext)
    
def runtests(title, testsource, outfilename, htmlfilename, order=True, screen=False):
    skipped = 0
    if type(testsource) is list:
        tests = testsource
    else:
        tests = []
        test_in_file = open(testsource)
        for tline in test_in_file:
            (passage, orig, expected, comment) = (tline.rstrip('\n').split('\t'))
            this_test = maketest(orig=orig, passage=passage, expected=expected, comment=comment)
            if this_test != None:
                tests.append(this_test)
            else:
                skipped += 1
        test_in_file.close()

    lines = []
    htmllines = []
    longlines = []
    nexact = 0
    ngood = 0
    ntests = len(tests)
    test_sequence = sorted(tests, key=lambda x: (x[1], x[2], x[0])) if order else tests

    for (i, (wset, expected, comment)) in enumerate(test_sequence):
        passage = get_passage(wset[-1])
        wss = partition_w(wset)
        orig = ''.join(get_orig(w, punct=True, set_pet=True, tetra=False) for w in wset)
        wordph = ''
        lex_info = ''
        dout = []
        for (j, ws) in enumerate(wss):
            this_lex_info = get_lex_info(ws[-1])
            (this_wordph, this_dout) = phono(ws, punct=not (j == len(wss) - 1), debug=True)
            wordph += this_wordph
            lex_info += this_lex_info
            dout.extend(this_dout)
        wordph = wordph.rstrip(' ')
        if wordph == expected:
            isgood = '='
            nexact += 1
        elif wordph.replace('ˌ', '').replace('ˈ', '').replace('-', '') ==              expected.replace('ˌ', '').replace('ˈ', '').replace('-', ''):
            isgood = '~'
            ngood += 1
        else:
            isgood = '#'
        line_text = '{:>3} {:<19} {:>6} {:<17} {:<22} {:<20} {} {:<20}'.format(
            i+1, passage, ws[-1],
            lex_info, orig, wordph,
            isgood,
            '' if isgood == '=' else expected, 
        )
        lines.append(line_text)
        if screen:
            if isgood in {'=', '~'}:
                print(line_text)
        if isgood not in {'=', '~'}:
            print(line_text)
        longlines.append('{:>3} {:<19} {:>6} {:<17} {:<25} => {:<25} < {} {:<25} # {}\n{}\n\n'.format(
            i+1, passage, ws[-1],
            lex_info, orig, wordph,
            isgood,
            '' if isgood == '=' else expected, 
            comment,
            '\n'.join('{:<7} {:<20} {}'.format('', x[0], x[1]) for x in dout),
        ))
        htmllines.append(('''
    <tr>
        <td class="{st}">{i}</td>
        <td class="v">{v} {w}</td>
        <td class="t">{t}</td>        
        <td class="h">{h}</td>
        <td class="l">{l}</td>
        <td class="p {st}">{p}</td>
        <td class="p{est}">{e}</td>
        <td class="c">{c}</td>
    </tr>
    ''').format(
        st='exact' if isgood == '=' else 'good' if isgood == '~' else 'error',
        i=i+1,
        v=passage, w='' if w == None else w,
        t=h_esc(orig),
        l=lex_info,
        h=get_hebrew(orig),
        p=wordph,
        e='' if isgood == '=' else expected,
        est='' if isgood == '=' else ' ca' if isgood == '~' else ' norm',
        c=h_esc(comment),
    ))

    line_text = '\n'.join(lines)
    longline_text = '\n'.join(longlines)
    test_out_file = open(vfname(outfilename), 'w')
    test_out_file.write('{}\n\n{}\n'.format(line_text, longline_text))
    stats = '{} tests; {} skipped; {} failed; {} passed of which {} exactly.'.format(
        ntests + skipped, skipped, ntests-ngood-nexact, ngood + nexact, nexact,
    )
    test_out_file.close()
    test_html_file = open(vfname(htmlfilename), 'w')
    test_html_headline = '''
    <tr>
        <th class="v">v</th>
        <th class="v">verse</th>
        <th class="t">etcbc</th>
        <th class="h">hebrew</th>
        <th class="l">lexical</th>
        <th class="p">phono</th>
        <th class="p norm">expected</th>
        <th class="c">comment</th>
    </tr>
    '''
    test_html_file.write('{}{}{}{}'.format(
        test_html_head(title, stats, ''), test_html_headline, ''.join(htmllines), test_html_tail))
    test_html_file.close()
    msg(stats)


# ### Produce showcases
# 
# This is a variant on ``runtests()``.
# 
# It produces overviews of the cases where the corpus dependent rules have been applied.

# In[34]:

def showcases(title, stats, testsource, order=True):
    ctitle = title+' cases'
    ttitle = title+' tests'
    fctitle = ctitle.replace(' ', '_')
    fttitle = ttitle.replace(' ', '_')
    test_file_name = my_file(vfname(fttitle+'.txt'))
    html_file_name = vfname(fctitle+'.html')

    msg("Generating HTML in {}".format(html_file_name))
    msg("Generating test set {} in {}".format(title, test_file_name))

    htmllines = []
    ncorr = 0
    test_sequence = sorted(
        testsource, key=lambda x: (x[3], x[0], x[1], x[5])
    ) if order else testsource
    ntests = len(testsource)

    test_file = open(test_file_name, 'w')
    for (i, (corr, wordph, wordph_c, lex, orig, w, comment)) in enumerate(test_sequence):
        passage = get_passage(w)
        lex_info = get_lex_info(w)
        test_file.write('{}\t{}\t{}\t{}\n'.format(
            passage,
            orig,
            wordph_c,
            comment,
        ))
        heb = get_hebrew(orig)
        if corr:
            ncorr += 1
        htmllines.append(('''
    <tr>
        <td class="v">{i}</td>
        <td class="cor{st}">{cr}</td>
        <td class="tl">{tl}</td>        
        <td class="v">{v} {w}</td>
        <td class="l">{l}</td>
        <td class="h">{h}</td>
        <td class="p {st}">{p}</td>
        <td class="p {st1}">{pc}</td>
        <td class="t">{t}</td>        
        <td class="c">{c}</td>
    </tr>
''').format(
        i=i+1,
        st=' cr' if corr else '',
        st1=' good' if corr else '',
        cr=corr,
        tl=h_esc(lex),
        v=passage, w='' if w == None else w,
        l=lex_info,
        h=heb,
        p=wordph if wordph != wordph_c else '',
        pc=wordph_c,
        t=h_esc(orig),
        c=h_esc(comment),
    ))
    test_file.close()

    mystats = '{} occurrences and {} corrections'.format(
        ntests, ncorr,
    )
    test_html_headline = '''
    <tr>
        <th class="v">n</th>
        <th class="cor cr">correction</th>
        <th class="tl">lexeme</th>
        <th class="v">verse</th>
        <th class="l">lexical</th>
        <th class="h">hebrew</th>
        <th class="p cr">phono<br/>uncorrected</th>
        <th class="p good">phono<br/>corrected</th>
        <th class="t">etcbc</th>
        <th class="c">comment</th>
    </tr>
    '''
    test_html_file = open(html_file_name, 'w')
    test_html_file.write('{}{}{}{}'.format(
        test_html_head(ctitle, stats, mystats), test_html_headline, ''.join(htmllines), test_html_tail))
    test_html_file.close()
    if stats: msg(stats)
    if mystats: msg(mystats)


# ## Test the existing examples

# In[35]:

for tname in [
    'mixed',
    'qamets_nonverb_tests',
    'qamets_verb_tests',
    'qamets_prs_tests',
]:
    runtests(
        tname, '{}.txt'.format(tname), 
        '{}_debug.txt'.format(tname), 
        '{}.html'.format(tname), 
        screen=False,
    )


# ### Testing: Special cases

# In[36]:

special_tests = [
    dict(passage='Joel 1:17', orig='<@B:C74W.', comment='qamets gadol or qatan'),
    dict(ws=7494, expected=None, comment="schwa in front of BGDKPT without dagesh"),
    dict(ws=5, expected=None, comment="article in isolation"),
    dict(ws=6, expected=None, comment="word after article in isolation"),
    dict(ws=106, expected=None, comment="proclitic min"),
    dict(ws=107, expected=None, comment="word starting with BGDKPT after proclitic min"),
    dict(passage='Genesis 1:7', orig='MI-T.A74XAT', expected=None, comment="proclitic min combined with word starting with BGDKPT"),
    dict(ws=1684, expected=None, comment='Tetra with end of verse'),
    dict(passage='Genesis 4:1', orig='J:HW@75H00', expected=None, comment='Tetra with end of verse'),
    dict(ws=27477, expected=None, comment="pronominal suffix after verb"),
    dict(ws=155387, expected=None, comment="peculiar representation of tetragrammaton"),
    dict(passage='Proverbia 10:10', orig='<AY.@92BET', expected=None, comment="the qamets should be gadol"),
    dict(passage='Genesis 9:21', orig='*>HLH', expected=None, comment='ketiv qere'),
]

compiled_tests = []
for t in special_tests:
    this_test = maketest(**t)
    if this_test != None:
        compiled_tests.append(this_test)

runtests(
    'special cases',
    compiled_tests, 
    'special_cases_out.txt', 'special_cases.html',
    screen=True,
)


# ## Making new tests: Qamets gadol qatan: non-verbs
# 
# We have generated a number of corrections of the qamets interpretation in non verbs. We have applied exceptions to the corrections. Here is the list of representative occurrences where corrections and/or exceptions have been applied.

# In[37]:

### msg('Showing lexemes with varied occurrences')
qqi_filename = 'qamets_qatan_individuals'
qqi = outfile('{}.txt'.format(qqi_filename))
nvcases = []

noccs = 0
ncorrs = 0
for lex in sorted(qq_varied):
    if lex not in qq_varied_remaining: continue
    occs = qq_varied[lex]
    for (skel, fullskel, w) in sorted(occs, key=lambda x: (x[1], x[2])):
        orig = get_orig(w, punct=False, tetra=False)
        wordq = phono(w, punct=False, correct=-1)
        corr = qamets_corrections.get(wordq, '')
        if corr: ncorrs += 1
        noccs += 1
        wordph = phono(w, punct=False, correct=0)
        wordph_c = phono(w, punct=False, correct=1)
        comment = 'on the basis of other occurrences' if corr else 'by the rules'
        qqi.write('{:<1}\t{:<5}\t{:<16}\t{:<16}\t{:<10}\t{:<20}\t{}\n'.format(
            '*' if corr else '',
            corr,
            wordph,
            wordph_c,
            lex,
            orig,
            w,
        ))
        nvcases.append((corr, wordph, wordph_c, lex, orig, w, comment))
    qqi.write('\n')
qqi.close()
msg('{} lexemes with {} occurrences and {} corrections written'.format(
    len(qq_varied_remaining), noccs, ncorrs,
))
showcases(
    'qamets nonverb',
    '{} lexemes'.format(len(qq_varied_remaining)),
    nvcases, 
    order=False,
)


# ## Making new tests: Qamets gadol qatan: verbs
# 
# Usually, accents take care that potential qatans are read as gadols.
# But sometimes the accents are missing.
# We have used a list of paradigm labels where such cases might occur, and there we suppress the gamets-as-qatan interpretation.
# We look at the verb paradigms to fill in the missing information.
# 
# Here we list the cases where this occurs, and show them.
# 
# ### Look up the cases

# In[38]:

qq_verb_words = set()
qq_verb_specials = []

msg('Finding qamets qatan special verb cases')
for w in F.otype.s('word'):
    ln = F.language.v(w)
    if ln != 'Hebrew': continue
    sp = F.sp.v(w)
    if sp != 'verb': continue
    orig = get_orig(w, punct=False, tetra=False)
    if '@' not in orig: continue   # no qamets in word
    word = doaccents(orig)
    wordq = doplainqamets(word, accentless=True)
    if '^' not in wordq: continue  # no risk of unwanted qamets qatan
#    if '!' in word: continue       # primary accent has been marked

    lex_info = get_lex_info(w)
    decl = get_decl(lex_info)
    if decl in qamets_qatan_verb_x:
        if (word, lex_info) in qq_verb_words: continue
        qq_verb_words.add((word, lex_info))
        qq_verb_specials.append((w, orig, word))
msg('{} cases'.format(len(qq_verb_specials)))


# ### Show the cases

# In[39]:

msg('Showing verb cases')

ncorr = 0
ngood = 0
vcases = []
verb_lexemes = set()
for (w, orig, word) in qq_verb_specials:
    wordph = phono(w, punct=False)
    wordph_ns = phono(w, punct=False, suppress_in_verb=False)
    corr = ''
    lex = F.lex.v(w)
    verb_lexemes.add(lex)
    if wordph == wordph_ns: 
        ngood += 1
        corr = ''
        comment = "qamets: no need to suppress qatan"
    else:
        ncorr += 1
        corr = 'gadol'
        comment = 'qamets: gadol maintained because of verb paradigm'
    vcases.append((corr, wordph_ns, wordph, lex, orig, w, comment))

showcases(
    'qamets verb',
    '{} lexemes'.format(len(verb_lexemes)),
    vcases,
    order=True,
)


# ## Making new tests: Qamets gadol qatan: pronominal suffixes
# 
# Usually, rules involving closed unaccented syllables trigger the qatan interpretation of a qamets.
# But in pronominal suffixes a qamets is always gadol.
# We detect these cases and suppress the gamets-as-qatan interpretation there.
# 
# ### Look up the cases

# In[40]:

qq_prs_words = set()
qq_prs_specials = []

msg('Finding qamets qatan in pronominal suffixes')
for w in F.otype.s('word'):
    ln = F.language.v(w)
    if ln != 'Hebrew': continue
    lex_info = get_lex_info(w)
    prs = get_prs(lex_info)
    if prs == '' : continue
    orig = get_orig(w, punct=False, tetra=False)
    if '@' not in prs: continue   # no qamets in suffix
    word = doaccents(orig)
    wordq = doplainqamets(word, accentless=False)
    if '^' not in wordq: continue  # no risk of unwanted qamets qatan
    if (word, lex_info) in qq_prs_words: continue
    qq_prs_words.add((word, lex_info))
    qq_prs_specials.append((w, orig, word))
msg('{} potential cases'.format(len(qq_prs_specials)))


# ### Show the cases

# In[41]:

msg('Showing prs cases')

ncorr = 0
ngood = 0
pcases = []
prs_lexemes = set()
for (w, orig, word) in qq_prs_specials:
    lex = F.lex.v(w)
    prs_lexemes.add(lex)
    wordph = phono(w)
    wordph_ns = phono(w, suppress_in_prs=False)
    corr = ''
    if wordph == wordph_ns: 
        ngood += 1
        corr = ''
        comment = "qamets: no need to suppress qatan"
    else:
        ncorr += 1
        corr = 'gadol'
        comment = 'qamets: gadol maintained in pronominal suffix'
    pcases.append((corr, wordph_ns, wordph, lex, orig, w, comment))

showcases(
    'qamets prs',
    '{} lexemes'.format(len(prs_lexemes)),
    pcases,
    order=True,
)


# # Print the whole text

# In[42]:

def stats_prog(): return ' '.join(str(stats.get(stat, 0)) for stat in interesting_stats)
        
msg('Generating complete texts (transcribed and phonetic) ... ')

phono_fname = 'phono{}.txt'.format(version)
word_dir = '{}/{}'.format(API['data_dir'], 'ph')
if not os.path.exists(word_dir): os.makedirs(word_dir)

word_fname = '{}/phono.{}{}'.format(word_dir, source, version)
phono_file = outfile(phono_fname)
word_file = open(word_fname, 'w')

orig_file = outfile('orig{}.txt'.format(version))
combi_file = open('combi{}.txt'.format(version), 'w')

stats = collections.Counter()
nv = 0
nchunk = 1000
nvc = 0
for v in F.otype.s('verse'):
    nv += 1
    nvc += 1
    if nvc == nchunk:
        msg('{:>5} verses {}'.format(nv, stats_prog()))
        nvc = 0
    passage_label = get_passage(v)
    phono_file.write('{}  '.format(passage_label))
    orig_file.write('{}  '.format(passage_label))
    combi_file.write('{}\n'.format(passage_label))

    words = partition_w(L.d('word', v))
    origs = []
    phonos = []
    
    for ws in words:
        lws = len(ws)
        orig_w = ''.join(get_orig(w, punct=True, set_pet=True, tetra=False) for w in ws)
        phono_w = phono(ws, inparts=True, count=True)
        origs.append(orig_w)
        phonos.extend(phono_w)
        for (i, w) in enumerate(ws):
            (real_phono, sep) = phono_sep.fullmatch(phono_w[i]).groups()
            word_file.write('{}\t{}\t{}\n'.format(w, real_phono, sep))

    orig_text = ''.join(origs)
    phono_text = ''.join(phonos)
    if not phono_text.endswith('.'): word_file.write('{}\t{}\t{}\n'.format('', '', '+'))
    orig_file.write('{}\n'.format(orig_text))
    phono_file.write('{}\n'.format(phono_text))
    combi_file.write('{}\n{}\n\n'.format(orig_text, phono_text))

phono_file.close()
orig_file.close()
combi_file.close()
word_file.close()
msg('{:>5} verses done {}'.format(nv, stats_prog()))
for stat in sorted(stats):
    amount = stats[stat]
    print('{:<1} {:>6} {}'.format(
        '#' if amount == 0 else '',
        amount,
        stat,
    ))


# ## Consistency check
# 
# We take the just generated phono and wordph files.
# From the phono file we strip the passage indicators, and from the wordph we strip the node numbers.
# 
# They should be consistent.

# In[45]:

phono_file = infile(phono_fname)
word_file = open(word_fname)

strip_passage = re.compile('^\S+ [0-9]+:[0-9]+\s*')

phono_test = []
msg("Reading phono")
i = 0
for line in phono_file:
    i += 1
    phono_test.append(strip_passage.sub('', line))
phono_file.close()
msg('{} lines'.format(i))

word_test = []
msg("Reading wordph")
i = 0
for line in word_file:
    (mat, sep) = line[0:-1].split('\t')[1:3]
    rsep = '' if sep == '+' else sep
    word_test.append(mat+rsep)
    if '.' in sep or '+' in sep:
        word_test.append('\n')
        i += 1
word_file.close()
msg('{} lines'.format(i))

phono_text = ''.join(phono_test)
word_text = ''.join(word_test)
if phono_text != word_text:
    print('ERROR: phono text and word info are NOT consistent')
else:
    print('OK: phono text and word info are CONSISTENT')

phono_test_name = my_file('phono_x{}.txt'.format(version))
word_test_name = my_file('wordph_x{}.txt'.format(version))
with open(phono_test_name, 'w') as f: f.write(phono_text)
with open(word_test_name, 'w') as f: f.write(word_text)


# In[ ]:



