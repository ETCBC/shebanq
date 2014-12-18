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
    material=('''book chapter iid page mr qw tp''', {'': '''x 0 -1 -1 m q txt_p'''}),
    hebrewdata=('''
        ht hl tt tl gl
        wd1 wd1_subpos wd1_pos wd1_lang wd1_n
        wd2 wd2_gender wd2_gnumber wd2_person wd2_state wd2_tense wd2_stem
        sp sp_rela sp_n
        ph ph_det ph_fun ph_typ ph_n
        cl cl_dom cl_typ cl_n
        sn sn_n
    ''', {'': '''
        v v x x v
        v x v x x
        v v v v v v v
        v v v
        v v v v v
        v v v v
        v v
    '''}),
    highlights=('''get active sel_one''', dict(q='x hlcustom grey', w='x hlcustom gray')),
    colormap=('0', dict(q='white', w='black')),
)
style = dict(
    q=dict(prop='background-color', default='grey', off='white', subtract=250, Tag='Query', tag='query', Tags='Queries', tags='queries'),
    w=dict(prop='color', default='gray', off='black', subtract=250, Tag='Word', tag='word', Tags='Words', tags='words'),
    m=dict(subtract=250, Tag='Item', tag='item', Tags='Items', tags='items'),
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
    for qw in init:
        initk = init[qw].strip().split()
        for (i, f) in enumerate(flds):
            settings[group][qw][f] = initk[i]

vcolor_proto = [tuple(vc.split(',')) for vc in vcolor_spec.strip().split()]
vdefaultcolors = [x[0] for x in vcolor_proto if x[3] == '1']
vcolornames = [x[0] for x in vcolor_proto]
vcolors = dict((x[0], dict(q=x[1], w=x[2])) for x in vcolor_proto)
ndefcolors = len(vdefaultcolors)

if nrows * ncols != len(vcolornames):
    print("View settings: mismatch in number of colors: {} * {} != {}".format(nrows, ncols, len(vcolornames)))
if dnrows * dncols != len(vdefaultcolors):
    print("View settings: mismatch in number of default colors: {} * {} != {}".format(dnrows, dncols, len(vdefaultcolors)))

def ccell(qw,iid,c): return '\t\t<td class="c{qw} {qw}{iid}">{n}</td>'.format(qw=qw,iid=iid,n=vcolornames[c])
def crow(qw,iid,r): return '\t<tr>\n{}\n\t</tr>'.format('\n'.join(ccell(qw,iid,c) for c in range(r * ncols, (r + 1) * ncols)))
def ctable(qw, iid): return '<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'.format(qw=qw,iid=iid, cs='\n'.join(crow(qw,iid,r) for r in range(nrows)))

def vsel(qw, iid, typ):
    content = '&nbsp;' if qw == 'q' else 'w'
    selc = '' if typ else '<span class="pickedc cc_selc_{qw}"><input type="checkbox" id="selc_{qw}{iid}" name="selc_{qw}{iid}"/></span>&nbsp;'
    sel = '<span class="picked cc_sel_{qw}" id="sel_{qw}{iid}">{lab}</span>'
    return (selc + sel).format (qw=qw,iid=iid, lab=content)

class Viewsettings():
    def __init__(self):
        self.this_legend = legend_tpl.format(base_doc=base_doc)
        self.state = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
        self.ignore = 'v' if 'ignore' in current.request.vars and current.request.vars['ignore'] == 'v' else 'x'
        for group in settings:
            self.state[group] = {}
            for qw in settings[group]:
                self.state[group][qw] = {}
                from_cookie = {}
                if self.ignore == 'x' and current.request.cookies.has_key(group+qw):
                    try:
                        from_cookie = json.loads(urllib.unquote(current.request.cookies[group+qw].value))
                    except ValueError: pass
                if group == 'colormap':
                    for x in from_cookie: self.state[group][qw][x] = from_cookie[x]
                    for x in current.request.vars:
                        xid = x[1:]
                        if xid.isdigit():
                            vstate = current.request.vars[x]
                            from_cookie[xid] = vstate
                            self.state[group][qw][xid] = vstate
                else:
                    for x in settings[group][qw]:
                        init = settings[group][qw][x]
                        vstate = current.request.vars[qw+x]
                        if vstate == None and self.ignore == 'x': vstate = from_cookie.get(x, init) 
                        from_cookie[x] = vstate
                        self.state[group][qw][x] = vstate

                current.response.cookies[group+qw] = urllib.quote(json.dumps(from_cookie))
                current.response.cookies[group+qw]['expires'] = 30 * 24 * 3600
                current.response.cookies[group+qw]['path'] = '/'

    def legend(self): return self.this_legend

    def dynamics(self):
        book_proto = current.request.vars.book
        return '''
var vcolors = {vcolors}
var vdefaultcolors = {vdefaultcolors}
var dncols = {dncols}
var dnrows = {dnrows}
var viewinit = {initstate}
var style = {style}
var ignore = {ignore}
dynamics()
'''.format(
    vdefaultcolors=json.dumps(vdefaultcolors),
    initstate=json.dumps(self.state),
    vcolors = json.dumps(vcolors),
    style = json.dumps(style),
    dncols = dncols,
    dnrows = dnrows,
    ignore = "'"+self.ignore+"'",
)

    def colorpicker(self, qw, iid, typ):
        return '{s}{p}\n'.format(s=vsel(qw, iid, typ), p=ctable(qw, iid))

text_tpl = u'''<table class="il c">
    <tr class="il ht"><td class="il ht"><span m="{word_number}" class="ht">{word_heb}</span></td></tr>
    <tr class="il hl"><td class="il hl"><span l="{lexicon_id}" class="hl">{word_vlex}</span></td></tr>
    <tr class="il tt"><td class="il tt"><span m="{word_number}" class="tt">{word_tran}</span></td></tr>
    <tr class="il tl"><td class="il tl"><span l="{lexicon_id}" class="tl">{word_lex}</span></td></tr>
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
    def __init__(self, passage_db, mr, verse_ids=None, chapter=None, tp=None):
        self.mr = mr
        self.tp = tp
        self.verses = []
        if self.mr == 'r' and (verse_ids == None or len(verse_ids) == 0): return
        verse_ids_str = ','.join((str(v) for v in verse_ids)) if verse_ids != None else None
        cfield = 'verse.id'
        cwfield = 'word_verse.verse_id'
        condition_pre = 'WHERE {{}} IN ({})'.format(verse_ids_str) if verse_ids != None else 'WHERE chapter_id = {}'.format(chapter) if chapter != None else ''
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)

        verse_info = passage_db.executesql('''
SELECT verse.id, book.name, chapter.chapter_num, verse.verse_num{} FROM verse
INNER JOIN chapter ON verse.chapter_id=chapter.id
INNER JOIN book ON chapter.book_id=book.id
{}
ORDER BY verse.id;
'''.format(', verse.xml' if tp == 'txt_p' else '', condition)) 

        word_records = []
        if tp == 'txt_il':
            word_records = passage_db.executesql('''
SELECT {}, verse_id, lexicon_id FROM word
INNER JOIN word_verse ON word_number = word_verse.anchor
INNER JOIN verse ON verse.id = word_verse.verse_id
{}
ORDER BY word_number;
'''.format(','.join(field_names), wcondition), as_dict=True)

        word_data = collections.defaultdict(lambda: [])
        for record in word_records:
            word_data[record['verse_id']].append(dict((x,h_esc(unicode(y), not x.endswith('_border'))) for (x,y) in record.items()))

        for v in verse_info:
            v_id = int(v[0])
            xml = v[4] if tp == 'txt_p' else ''
            self.verses.append(Verse(v[1], v[2], v[3], xml, word_data[v_id], tp=tp, mr=mr)) 

class Verse():

    def __init__(self, book_name, chapter_num, verse_num, xml, word_data, tp=None, mr=None):
        self.tp = tp
        self.mr = mr
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        self.xml = xml
        self.word_data = word_data
        self.words = []

    def to_string(self):
        return "{}\n{}".format(self.citation_ref(), self.text)

    def chapter_link(self):
        return (self.book_name, self.chapter_num)

    def label(self):
        if self.mr == 'm': return self.verse_num
        else:
            (book, chapter, verse) = (self.book_name, self.chapter_num, self.verse_num)
            pretty_book = book.replace('_', ' ')
            return ("{} {}:{}".format(pretty_book, chapter, verse), book, chapter)

    def get_words(self):
        if (len(self.words) == 0):
            root = ET.fromstring(u'<verse>{}</verse>'.format(self.xml).encode('utf-8'))
            for child in root:
                monad_id = int(child.attrib['m'])
                lex_id = int(child.attrib['l'])
                text = '' if child.text is None else child.text
                trailer = child.get('t', '')
                self.words.append((monad_id, lex_id, text, trailer))
        return self.words

    def material(self, user_agent):
        if self.tp == 'txt_p': return self._plain_text(user_agent)
        elif self.tp == 'txt_il': return self._rich_text(user_agent)
        
    def _plain_text(self, user_agent):
        material = []
        for word in self.get_words():
            atext = adapted_text(word[2], user_agent)
            material.append(u'''<span m="{}" l="{}">{}</span>{}'''.format(word[0], word[1], atext, word[3]))
        return ''.join(material)

    def _rich_text(self, user_agent):
        material = []
        for word in self.word_data:
            material.append(text_tpl.format(**word))
        return ''.join(material)

