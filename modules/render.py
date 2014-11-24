#!/usr/bin/env python
#-*- coding:utf-8 -*-

import collections
import json,urllib
import xml.etree.ElementTree as ET

from gluon import current

base_doc = 'http://shebanq-doc.readthedocs.org/en/latest/features/comments'

replace_set = {0x059C,0x05A8,0x05BD,0x05A9,0x0594,0x05A4,0x05B4,0x05B1,0x05A5,0x05A0,0x05A9,0x059D,0x0598,0x05B0,0x05BD,0x05B7,0x0595,0x059F,0x05B3,0x059B,0x05B2,0x05AD,0x05BB,0x05B6,0x05C4,0x05B8,0x0599,0x05AE,0x05A3,0x05C5,0x05B5,0x05A1,0x0591,0x0596,0x0593,0x05AF,0x05AB,0x05AC,0x059A,0x05A6,0x05BF,0x05AA,0x05A8,0x05A7,0x05A0,0x0597,0x059E,0x05BD}

nrows = 4
ncols = 4
dnrows = 3
dncols = 4

vcolor_spec = '''
    red,#ff0000,#ff0000,1 salmon,#ff6688,#ee7799,1 orange,#ffcc66,#eebb55,1 yellow,#ffff00,#dddd00,1
    green,#00ff00,#00bb00,1 spring,#ddff77,#77dd44,1 tropical,#66ffcc,#55ddbb,1 turquoise,#00ffff,#00eeee,1
    blue,#8888ff,#0000ff,1 skye,#66ccff,#55bbff,1 lilac,#cc88ff,#aa22ff,1 magenta,#ff00ff,#ee00ee,1
    grey,#eeeeee,#eeeeee,0 gray,#aaaaaa,#aaaaaa,0 black,#000000,#000000,0 white,#ffffff,#ffffff,0
'''

field_names = '''
    word_heb word_vlex word_tran word_lex word_gloss
    word_subpos word_pos word_lang word_number
    word_gender word_gnumber word_person word_state word_tense word_stem
    subphrase_border subphrase_number subphrase_rela
    phrase_border phrase_number phrase_function phrase_typ phrase_det
    clause_border clause_number clause_typ clause_txt
    sentence_border sentence_number
'''.strip().split()

specs = dict(
    hebrewdata=('''
        ht hl tt tl gl
        wd1 wd1_subpos wd1_pos wd1_lang wd1_n
        wd2 wd2_gender wd2_gnumber wd2_person wd2_state wd2_tense wd2_stem
        sp sp_rela sp_n
        ph ph_det ph_fun ph_typ ph_n
        cl cl_dom cl_typ cl_n
        sn sn_n
        txt_p txt_il
    ''', {'': '''
        v v x x v
        v x v x x
        v v v v v v v
        v v v
        v v v v v
        v v v v
        v v
        v x
    '''}),
    hlview=('''get active sel_one''', dict(q='x hlmy grey', w='x hlmy gray')),
    cmap=('0', dict(q='white', w='black'))
)
style = dict(
    q=dict(prop='background-color', off='#ffffff'),
    w=dict(prop='color', off='#000000'),
)

legend_tpl = '''
<table id="legend" class="il">
    <tr class="il l_ht"><td class="c l_ht"><input
    type="checkbox" id="ht" name="ht"/></td><td
    class="il l_ht"><a target="_blank" href="{base_doc}/g_word_utf8.html"><span class="l_ht">text כתף</span></a></td></tr>
    <tr class="il l_hl"><td class="c l_hl"><input
    type="checkbox" id="hl" name="hl"/></td><td
    class="il l_hl"><a target="_blank" href="{base_doc}/vocalized_lexeme.html"><span class="l_hl">lexeme דבר</span></a></td></tr>
    <tr class="il l_tt"><td class="c l_tt"><input
    type="checkbox" id="tt" name="tt"/></td><td
    class="il l_tt"><a target="_blank" href="{base_doc}/g_word.html"><span class="l_tt">text</span></a></td></tr>
    <tr class="il l_tl"><td class="c l_tl"><input
    type="checkbox" id="tl" name="tl"/></td><td
    class="il l_tl"><a target="_blank" href="{base_doc}/g_lex.html"><span class="l_tl">lexeme</span></a></td></tr>
    <tr class="il l_gl"><td class="c l_gl"><input
    type="checkbox" id="gl" name="gl"/></td><td
    class="il l_gl"><a target="_blank" href="{base_doc}/gloss.html"><span class="l_gl">gloss</span></a></td></tr>
    <tr class="il l_wd1"><td class="c l_wd1"><input
    type="checkbox" id="wd1" name="wd1"/></td><td
    class="il l_wd1"><input type="checkbox" id="wd1_subpos" name="wd1_subpos"/><a target="_blank" href="{base_doc}/ls.html"><span
    class="il l_wd1_subpos">lexical set</span></a>&nbsp;<input type="checkbox" id="wd1_pos" name="wd1_pos"/><a target="_blank" href="{base_doc}/sp.html"><span
    class="il l_wd1_pos">part-of-speech</span></a>&nbsp;<input type="checkbox" id="wd1_lang" name="wd1_lang"/><a target="_blank" href="{base_doc}/language.html"><span
    class="il l_wd1_lang">language</span></a>&nbsp;<input type="checkbox" id="wd1_n" name="wd1_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_wd1_n">monad#</span></a></td></tr>
    <tr class="il l_wd2"><td class="c l_wd2"><input
    type="checkbox" id="wd2" name="wd2"/></td><td
    class="il l_wd2"><input type="checkbox" id="wd2_gender" name="wd2_gender"/><a target="_blank" href="{base_doc}/gn.html"><span
    class="il l_wd2_gender">gender</span></a>&nbsp;<input type="checkbox" id="wd2_gnumber" name="wd2_gnumber"/><a target="_blank" href="{base_doc}/nu.html"><span
    class="il l_wd2_gnumber">number</span></a>&nbsp;<input type="checkbox" id="wd2_person" name="wd2_person"/><a target="_blank" href="{base_doc}/ps.html"><span
    class="il l_wd2_person">person</span></a>&nbsp;<input type="checkbox" id="wd2_state" name="wd2_state"/><a target="_blank" href="{base_doc}/st.html"><span
    class="il l_wd2_state">state</span></a>&nbsp;<input type="checkbox" id="wd2_tense" name="wd2_tense"/><a target="_blank" href="{base_doc}/vt.html"><span
    class="il l_wd2_tense">tense</span></a>&nbsp;<input type="checkbox" id="wd2_stem" name="wd2_stem"/><a target="_blank" href="{base_doc}/vs.html"><span
    class="il l_wd2_stem">verbal stem</span></a></td></tr>
    <tr class="il l_sp"><td class="c l_sp"><input
    type="checkbox" id="sp" name="sp"/></td><td
    class="il l_sp"><input type="checkbox" id="sp_rela" name="sp_rela"/><a target="_blank" href="{base_doc}/rela.html"><span
    class="il l_sp_rela">relation</span></a>&nbsp;<input type="checkbox" id="sp_n" name="sp_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_sp_n">subphrase#</span></a></td></tr>
    <tr class="il l_ph"><td class="c l_ph"><input
    type="checkbox" id="ph" name="ph"/></td><td
    class="il l_ph"><input type="checkbox" id="ph_det" name="ph_det"/><a target="_blank" href="{base_doc}/det.html"><span
    class="il l_ph_det">determination</span></a>&nbsp;<input type="checkbox" id="ph_fun" name="ph_fun"/><a target="_blank" href="{base_doc}/function.html"><span
    class="il l_ph_fun">function</span></a>&nbsp;<input type="checkbox" id="ph_typ" name="ph_typ"/><a target="_blank" href="{base_doc}/typ.html"><span
    class="il l_ph_typ">type</span></a>&nbsp;<input type="checkbox" id="ph_n" name="ph_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_ph_n">phrase#</span></a></td></tr>
    <tr class="il l_cl"><td class="c l_cl"><input
    type="checkbox" id="cl" name="cl"/></td><td
    class="il l_cl"><input type="checkbox" id="cl_dom" name="cl_dom"/><a target="_blank" href="{base_doc}/domain.html"><span
    class="il l_cl_dom">domain</span></a>&nbsp;<input type="checkbox" id="cl_typ" name="cl_typ"/><a target="_blank" href="{base_doc}/typ.html"><span
    class="il l_cl_typ">type</span></a>&nbsp;<input type="checkbox" id="cl_n" name="cl_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_cl_n">clause#</span></a></td></tr>
    <tr class="il l_sn"><td class="c l_sn"><input
    type="checkbox" id="sn" name="sn"/></td><td
    class="il l_sn"><input type="checkbox" id="sn_n" name="sn_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_sn_n">sentence#</span></a></td></tr>
</table>
'''

settings = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
for group in specs:
    (flds, init) = specs[group]
    flds = flds.strip().split()
    for k in init:
        initk = init[k].strip().split()
        for (i, f) in enumerate(flds):
            settings[group][k][f] = initk[i]

vcolor_proto = [tuple(vc.split(',')) for vc in vcolor_spec.strip().split()]
vdefaultcolors = [x[0] for x in vcolor_proto if x[3] == '1']
vcolornames = [x[0] for x in vcolor_proto]
vcolors = dict((x[0], dict(q=x[1], w=x[2])) for x in vcolor_proto)
ndefcolors = len(vdefaultcolors)

if nrows * ncols != len(vcolornames):
    print("View settings: mismatch in number of colors: {} * {} != {}".format(nrows, ncols, len(vcolornames)))
if dnrows * dncols != len(vdefaultcolors):
    print("View settings: mismatch in number of default colors: {} * {} != {}".format(dnrows, dncols, len(vdefaultcolors)))

def vdef(vid):
    mod = vid % ndefcolors
    return vdefaultcolors[dncols * (mod % dnrows) + int(mod / dnrows)]

def ccell(k,vid,c): return '\t\t<td class="cc cc{k} {k}{vid}">{n}</td>'.format(k=k,vid=vid,n=vcolornames[c])
def crow(k,vid,r): return '\t<tr>\n{}\n\t</tr>'.format('\n'.join(ccell(k,vid,c) for c in range(r * ncols, (r + 1) * ncols)))
def ctable(k, vid): return '<table class="picker" id="picker{k}_{vid}">\n{cs}\n</table>\n'.format(k=k,vid=vid, cs='\n'.join(crow(k,vid,r) for r in range(nrows)))

def vsel(k, vid, defn, typ):
    content = '&nbsp;' if k == 'q' else 'w'
    tstart = '<table class="picked"><tr>'
    tend = '</tr></table>\n'
    selc = '' if typ else '<td class="cc_selc{k}"><input type="checkbox" id="selc{k}_{vid}" name="selc{k}_{vid}"/></td>'
    sel = '<td class="cc_sel{k}" id="sel{k}_{vid}" defn="{dn}">{lab}</td>'
    return (tstart + selc + sel + tend).format (k=k,vid=vid, dn=defn, lab=content)

class Viewsettings():
    def __init__(self, page_kind, vid=None):
        self.page_kind = page_kind
        self.vid = vid
        self.this_legend = legend_tpl.format(base_doc=base_doc)
        self.state = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
        for group in settings:
            self.state[group] = {}
            for k in settings[group]:
                self.state[group][k] = {}
                from_cookie = {}
                if current.request.cookies.has_key(group+k):
                    try:
                        from_cookie = json.loads(urllib.unquote(current.request.cookies[group+k].value))
                    except ValueError: pass
                if group == 'cmap':
                    for x in from_cookie: self.state[group][k][x] = from_cookie[x]
                    for x in current.request.vars:
                        if x[0] == k and x[1:].isdigit():
                            vstate = current.request.vars[x]
                            from_cookie[x[1:]] = vstate
                            self.state[group][k][x] = vstate
                else:
                    for x in settings[group][k]:
                        init = settings[group][k][x]
                        vstate = current.request.vars[k+x]
                        if vstate == None: vstate = from_cookie.get(x, init) 
                        from_cookie[x] = vstate
                        self.state[group][k][x] = vstate

                current.response.cookies[group+k] = urllib.quote(json.dumps(from_cookie))
                current.response.cookies[group+k]['expires'] = 30 * 24 * 3600
                current.response.cookies[group+k]['path'] = '/'

    def legend(self): return self.this_legend

    def init_view(self):
        return '''
var vcolors = {vcolors}
var viewstate = {initstate}
var style = {style}
var pagekind = '{pagekind}'
var thebook = '{book}'
var thechapter = {chapter}
var thevid = {vid}
init_page()
'''.format(
    initstate=json.dumps(self.state),
    vcolors = json.dumps(vcolors),
    style = json.dumps(style),
    pagekind = self.page_kind,
    book = current.request.vars.book or '',
    chapter = current.request.vars.chapter or 0,
    vid = 'null' if self.vid == None else self.vid,
)

    def refresh_verses(self):
        return '''
refresh_verses()
    '''

    def colorpicker(self, k, vid, typ):
        defn = settings['hlview'][k]['sel_'+vid] if typ else vdef(vid)
        return '{s}{p}\n'.format(s=vsel(k, vid, defn, typ), p=ctable(k, vid))

text_tpl = u'''<table class="il c">
    <tr class="il ht"><td class="il ht"><span m="{word_number}" class="ht">{word_heb}</span></td></tr>
    <tr class="il hl"><td class="il hl"><span class="hl">{word_vlex}</span></td></tr>
    <tr class="il tt"><td class="il tt"><span m="{word_number}" class="tt">{word_tran}</span></td></tr>
    <tr class="il tl"><td class="il tl"><span class="tl">{word_lex}</span></td></tr>
    <tr class="il gl"><td class="il gl"><span class="gl">{word_gloss}</span></td></tr>
    <tr class="il wd1"><td class="il wd1"><span class="il wd1_subpos">{word_subpos}</span>&nbsp;<span class="il wd1_pos">{word_pos}</span>&nbsp;<span class="il wd1_lang">{word_lang}</span>&nbsp;<span class="n wd1_n">{word_number}</span></td></tr>
    <tr class="il wd2"><td class="il wd2"><span class="il wd2_gender">{word_gender}</span>&nbsp;<span class="il wd2_gnumber">{word_gnumber}</span>&nbsp;<span class="il wd2_person">{word_person}</span>&nbsp;<span class="il wd2_state">{word_state}</span>&nbsp;<span class="il wd2_tense">{word_tense}</span>&nbsp;<span class="il wd2_stem">{word_stem}</span></td></tr>
    <tr class="il sp"><td class="il sp {subphrase_border}"><span class="il sp_rela">{subphrase_rela}</span>&nbsp;<span class="n sp_n">{subphrase_number}</span></td></tr>
    <tr class="il ph"><td class="il ph {phrase_border}"><span class="il ph_det">{phrase_det}</span>&nbsp;<span class="il ph_fun">{phrase_function}</span>&nbsp;<span class="il ph_typ">{phrase_typ}</span>&nbsp;<span class="n ph_n">{phrase_number}</span></td></tr>
    <tr class="il cl"><td class="il cl {clause_border}"><span class="il cl_dom">{clause_txt}</span>&nbsp;<span class="il cl_typ">{clause_typ}</span>&nbsp;<span class="n cl_n">{clause_number}</span></td></tr>
    <tr class="il sn"><td class="il sn {sentence_border}"><span class="n sn_n">{sentence_number}</span></td></tr>
</table>'''

def adapted_text(text, user_agent): return '' if text == '' else (text + ('&nbsp;' if ord(text[-1]) in replace_set else '')) if user_agent == 'Chrome' else text

def h_esc(material, fill=True):
    material = material.replace(
        '&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot').replace(
        "'", '&apos;').replace('\\n', '\n')
    if fill:
        if material == '': material = '&nbsp;'
    return material

class Verses():
    def __init__(self, passage_db, page_kind, verse_ids=None, chapter=None):
        self.page_kind = page_kind
        self.verses = []
        verse_ids_str = ','.join((str(v) for v in verse_ids)) if verse_ids != None else None
        cfield = 'verse.id'
        cwfield = 'word_verse.verse_id'
        condition_pre = 'WHERE {{}} IN ({})'.format(verse_ids_str) if verse_ids != None else 'WHERE chapter_id = {}'.format(chapter) if chapter != None else ''
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)

        verse_info = passage_db.executesql('''
SELECT verse.id, book.name, chapter.chapter_num, verse.verse_num, verse.xml FROM verse
INNER JOIN chapter ON verse.chapter_id=chapter.id
INNER JOIN book ON chapter.book_id=book.id
{}
ORDER BY verse.id;
'''.format(condition)) 

        word_records = passage_db.executesql('''
SELECT {}, verse_id FROM word
INNER JOIN word_verse ON word_number = word_verse.anchor
INNER JOIN verse ON verse.id = word_verse.verse_id
{}
ORDER BY word_number;
'''.format(','.join(field_names), wcondition), as_dict=True)

        word_data = collections.defaultdict(lambda: [])
        for record in word_records:
            word_data[record['verse_id']].append(dict((k,h_esc(unicode(v), not k.endswith('_border'))) for (k,v) in record.items()))

        for v in verse_info:
            v_id = int(v[0])
            self.verses.append(Verse(v[1], v[2], v[3], v[4], word_data[v_id])) 

class Verse():

    def __init__(self, book_name, chapter_num, verse_num, xml, word_data):
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        self.xml = xml
        self.word_data = word_data
        self.words = []

    def to_string(self):
        return "{}\n{}".format(self.citation_ref(), self.text)

    def citation_ref(self):
        return "{} {}:{}".format(self.book_name.replace('_', ' '), self.chapter_num, self.verse_num)

    def chapter_link(self):
        return (self.book_name, self.chapter_num)

    def get_words(self):
        if (len(self.words) is 0):
            root = ET.fromstring(u'<verse>{}</verse>'.format(self.xml).encode('utf-8'))
            for child in root:
                monad_id = int(child.attrib['m'])
                text = '' if child.text is None else child.text
                trailer = child.get('t', '')
                word = Word(monad_id, text, trailer)
                self.words.append(word)
        return self.words

    def plain_text(self, user_agent):
        material = []
        for word in self.get_words():
            atext = adapted_text(word.text, user_agent)
            material.append(u'''<span m="{}">{}</span>{}'''.format(word.monad_id, atext, word.trailer))
        return ''.join(material)

    def rich_text(self, user_agent):
        material = []
        for word in self.word_data:
            material.append(text_tpl.format(**word))
        return ''.join(material)


class Word():

    def __init__(self, monad_id, text, trailer):
        self.monad_id = monad_id
        self.text = text
        self.trailer = trailer

    def to_string(self):
        return "id:" + str(self.monad_id) + " text:" + self.text + " trailer:" + self.trailer

