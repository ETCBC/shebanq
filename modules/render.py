#!/usr/bin/env python
#-*- coding:utf-8 -*-

import collections
import json
import xml.etree.ElementTree as ET

base_doc = 'http://shebanq-doc.readthedocs.org/en/latest/features/comments'

replace_set = {0x059C,0x05A8,0x05BD,0x05A9,0x0594,0x05A4,0x05B4,0x05B1,0x05A5,0x05A0,0x05A9,0x059D,0x0598,0x05B0,0x05BD,0x05B7,0x0595,0x059F,0x05B3,0x059B,0x05B2,0x05AD,0x05BB,0x05B6,0x05C4,0x05B8,0x0599,0x05AE,0x05A3,0x05C5,0x05B5,0x05A1,0x0591,0x0596,0x0593,0x05AF,0x05AB,0x05AC,0x059A,0x05A6,0x05BF,0x05AA,0x05A8,0x05A7,0x05A0,0x0597,0x059E,0x05BD}

field_names = '''
word_number word_heb word_vlex word_tran word_lex word_gloss word_lang word_pos word_subpos word_tense word_stem word_gender word_gnumber word_person word_state subphrase_border subphrase_number subphrase_rela phrase_border phrase_number phrase_function phrase_typ phrase_det clause_border clause_number clause_typ clause_txt sentence_border sentence_number
'''.strip().split()

toggle_spec = '''
toggle_ht,1 toggle_hl,1 toggle_tt,0 toggle_tl,0 toggle_gl,1 toggle_wd1,1 toggle_wd1_subpos,0 toggle_wd1_pos,1 toggle_wd1_lang,0 toggle_wd1_n,0 toggle_wd2,1 toggle_wd2_gender,1 toggle_wd2_gnumber,1 toggle_wd2_person,1 toggle_wd2_state,1 toggle_wd2_tense,1 toggle_wd2_stem,1 toggle_sp,1 toggle_sp_rela,1 toggle_sp_n,1 toggle_ph,1 toggle_ph_det,1 toggle_ph_fun,1 toggle_ph_typ,1 toggle_ph_n,1 toggle_cl,1 toggle_cl_dom,1 toggle_cl_typ,1 toggle_cl_n,1 toggle_sn,1 toggle_sn_n,1 toggle_txt_p,1 toggle_txt_il,0
'''.strip().split()
toggle_proto = [tuple(tg.split(',')) for tg in toggle_spec]
toggles = [(x[0], x[1] == '1') for x in toggle_proto]

class Queries():
    qcolor_spec = '''#ff0000,red,1 #ff6688,salmon,1 #ffcc66,orange,1 #ffff00,yellow,1 #00ff00,green,1 #ccff66,spring,1 #66ffcc,tropical,1 #00ffff,turquoise,1 #8888ff,blue,1 #66ccff,skye,1 #cc44ff,lilac,1 #ff00ff,magenta,1 #eeeeee,grey,0 #aaaaaa,gray,0 #000000,black,0 #ffffff,white,0'''.strip().split()
    qcolor_proto = [tuple(qc.split(',')) for qc in qcolor_spec]
    qcolors = [x[0] for x in qcolor_proto]
    qcolornames = dict((x[0], x[1]) for x in qcolor_proto)
    qdefaultcolors = [x[0] for x in qcolor_proto if x[2] == '1']
    nrows = 4
    ncols = 4
    dnrows = 3
    dncols = 4
    ndefcolors = len(qdefaultcolors)

    def __init__(self):
        if Queries.nrows * Queries.ncols != len(Queries.qcolors):
            print("Query settings: mismatch in number of colors: {} * {} != {}".format(Queries.nrows, Queries.ncols, len(Queries.qcolors)))
        if Queries.dnrows * Queries.dncols != len(Queries.qdefaultcolors):
            print("Query settings: mismatch in number of default colors: {} * {} != {}".format(Queries.dnrows, Queries.dncols, len(Queries.qdefaultcolors)))

    @staticmethod
    def _qdef(qid):
        mod = qid % Queries.ndefcolors
        return Queries.qdefaultcolors[Queries.dncols * (mod % Queries.dnrows) + int(mod / Queries.dnrows)]

    @staticmethod
    def _ccell(qid,c):
        cc = Queries.qcolors[c]
        cn = Queries.qcolornames[cc]
        return '\t\t<td class="cc {qid}" style="background-color: {c}">{n}</td>'.format(qid=qid,c=cc,n=cn)

    @staticmethod
    def _crow(qid,r):
        return '\t<tr>\n{}\n\t</tr>'.format('\n'.join(Queries._ccell(qid,c) for c in range(r * Queries.ncols, (r + 1) * Queries.ncols)))

    @staticmethod
    def _ctable(qid):
        return '<table class="picker" id="picker_{qid}">\n{cs}\n</table>\n'.format(qid=qid, cs='\n'.join(Queries._crow(qid,r) for r in range(Queries.nrows)))

    @staticmethod
    def _qsel(qid, initn): return '<table class="picked"><tr><td class="cc_sel" id="sel_{qid}">{n}</td></tr></table>\n'.format(qid=qid, n=initn)

    def _js(self, qid, initc, monads):
        return 'jscolorpicker({qid}, "{ic}", {mn})\n'.format(qid=qid, ic=initc, mn='null' if monads == None else "'{}'".format(monads))

    def colorpicker(self, qid, initc=None,monads=None):
        if initc == None or initc not in Queries.qcolors:
            initc = Queries._qdef(qid)
        initn = Queries.qcolornames.get(initc, 'choose...')
        return '{s}{p}<script type="text/javascript">{j}</script>\n'.format(s=Queries._qsel(qid, initn), p=Queries._ctable(qid), j=self._js(qid, initc, monads))

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

legend_tpl = '''
<table class="il">
    <tr class="il l_ht"><td class="c l_ht"><input
    type="checkbox" id="toggle_ht" name="toggle_ht"/></td><td
    class="il l_ht"><a target="_blank" href="{base_doc}/g_word_utf8.html"><span class="l_ht">text כתף</span></a></td></tr>
    <tr class="il l_hl"><td class="c l_hl"><input
    type="checkbox" id="toggle_hl" name="toggle_hl"/></td><td
    class="il l_hl"><a target="_blank" href="{base_doc}/vocalized_lexeme.html"><span class="l_hl">lexeme דבר</span></a></td></tr>
    <tr class="il l_tt"><td class="c l_tt"><input
    type="checkbox" id="toggle_tt" name="toggle_tt"/></td><td
    class="il l_tt"><a target="_blank" href="{base_doc}/g_word.html"><span class="l_tt">text</span></a></td></tr>
    <tr class="il l_tl"><td class="c l_tl"><input
    type="checkbox" id="toggle_tl" name="toggle_tl"/></td><td
    class="il l_tl"><a target="_blank" href="{base_doc}/g_lex.html"><span class="l_tl">lexeme</span></a></td></tr>
    <tr class="il l_gl"><td class="c l_gl"><input
    type="checkbox" id="toggle_gl" name="toggle_gl"/></td><td
    class="il l_gl"><a target="_blank" href="{base_doc}/gloss.html"><span class="l_gl">gloss</span></a></td></tr>
    <tr class="il l_wd1"><td class="c l_wd1"><input
    type="checkbox" id="toggle_wd1" name="toggle_wd1"/></td><td
    class="il l_wd1"><input type="checkbox" id="toggle_wd1_subpos" name="toggle_wd1_subpos"/><a target="_blank" href="{base_doc}/ls.html"><span
    class="il l_wd1_subpos">lexical set</span></a>&nbsp;<input type="checkbox" id="toggle_wd1_pos" name="toggle_wd1_pos"/><a target="_blank" href="{base_doc}/sp.html"><span
    class="il l_wd1_pos">part-of-speech</span></a>&nbsp;<input type="checkbox" id="toggle_wd1_lang" name="toggle_wd1_lang"/><a target="_blank" href="{base_doc}/language.html"><span
    class="il l_wd1_lang">language</span></a>&nbsp;<input type="checkbox" id="toggle_wd1_n" name="toggle_wd1_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_wd1_n">monad#</span></a></td></tr>
    <tr class="il l_wd2"><td class="c l_wd2"><input
    type="checkbox" id="toggle_wd2" name="toggle_wd2"/></td><td
    class="il l_wd2"><input type="checkbox" id="toggle_wd2_gender" name="toggle_wd2_gender"/><a target="_blank" href="{base_doc}/gn.html"><span
    class="il l_wd2_gender">gender</span></a>&nbsp;<input type="checkbox" id="toggle_wd2_gnumber" name="toggle_wd2_gnumber"/><a target="_blank" href="{base_doc}/nu.html"><span
    class="il l_wd2_gnumber">number</span></a>&nbsp;<input type="checkbox" id="toggle_wd2_person" name="toggle_wd2_person"/><a target="_blank" href="{base_doc}/ps.html"><span
    class="il l_wd2_person">person</span></a>&nbsp;<input type="checkbox" id="toggle_wd2_state" name="toggle_wd2_state"/><a target="_blank" href="{base_doc}/st.html"><span
    class="il l_wd2_state">state</span></a>&nbsp;<input type="checkbox" id="toggle_wd2_tense" name="toggle_wd2_tense"/><a target="_blank" href="{base_doc}/vt.html"><span
    class="il l_wd2_tense">tense</span></a>&nbsp;<input type="checkbox" id="toggle_wd2_stem" name="toggle_wd2_stem"/><a target="_blank" href="{base_doc}/vs.html"><span
    class="il l_wd2_stem">verbal stem</span></a></td></tr>
    <tr class="il l_sp"><td class="c l_sp"><input
    type="checkbox" id="toggle_sp" name="toggle_sp"/></td><td
    class="il l_sp"><input type="checkbox" id="toggle_sp_rela" name="toggle_sp_rela"/><a target="_blank" href="{base_doc}/rela.html"><span
    class="il l_sp_rela">relation</span></a>&nbsp;<input type="checkbox" id="toggle_sp_n" name="toggle_sp_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_sp_n">subphrase#</span></a></td></tr>
    <tr class="il l_ph"><td class="c l_ph"><input
    type="checkbox" id="toggle_ph" name="toggle_ph"/></td><td
    class="il l_ph"><input type="checkbox" id="toggle_ph_det" name="toggle_ph_det"/><a target="_blank" href="{base_doc}/det.html"><span
    class="il l_ph_det">determination</span></a>&nbsp;<input type="checkbox" id="toggle_ph_fun" name="toggle_ph_fun"/><a target="_blank" href="{base_doc}/function.html"><span
    class="il l_ph_fun">function</span></a>&nbsp;<input type="checkbox" id="toggle_ph_typ" name="toggle_ph_typ"/><a target="_blank" href="{base_doc}/typ.html"><span
    class="il l_ph_typ">type</span></a>&nbsp;<input type="checkbox" id="toggle_ph_n" name="toggle_ph_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_ph_n">phrase#</span></a></td></tr>
    <tr class="il l_cl"><td class="c l_cl"><input
    type="checkbox" id="toggle_cl" name="toggle_cl"/></td><td
    class="il l_cl"><input type="checkbox" id="toggle_cl_dom" name="toggle_cl_dom"/><a target="_blank" href="{base_doc}/domain.html"><span
    class="il l_cl_dom">domain</span></a>&nbsp;<input type="checkbox" id="toggle_cl_typ" name="toggle_cl_typ"/><a target="_blank" href="{base_doc}/typ.html"><span
    class="il l_cl_typ">type</span></a>&nbsp;<input type="checkbox" id="toggle_cl_n" name="toggle_cl_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_cl_n">clause#</span></a></td></tr>
    <tr class="il l_sn"><td class="c l_sn"><input
    type="checkbox" id="toggle_sn" name="toggle_sn"/></td><td
    class="il l_sn"><input type="checkbox" id="toggle_sn_n" name="toggle_sn_n"/><a target="_blank" href="{base_doc}/number.html"><span
    class="n l_sn_n">sentence#</span></a></td></tr>
</table>
'''

def adapted_text(text, user_agent): return '' if text == '' else (text + ('&nbsp;' if ord(text[-1]) in replace_set else '')) if user_agent == 'Chrome' else text

def h_esc(material, fill=True):
    material = material.replace(
        '&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot').replace(
        "'", '&apos;').replace('\\n', '\n')
    if fill:
        if material == '': material = '&nbsp;'
    return material

def viewlink(request, response, fresh=None):
    values = []
    for x in toggles:
        if x[0] == fresh:
            val = response.cookies[x[0]].value if response.cookies.has_key(x[0]) else 'False'
        else:
            val = request.cookies[x[0]].value if request.cookies.has_key(x[0]) else 'False'
        values.append('{}={}'.format(x[0], val))
    return '''<a id="yviewlink" href="#">show link to this view</a> <a id="xviewlink" href="#">hide link to this view</a>
<textarea readonly id="cviewlink">&{vars}</textarea>
<script type="text/javascript">jsviewlink("{vars}")</script>
'''.format(vars='&'.join(v for v in values))

class Verses():
    def __init__(self, passage_db, request, response, verse_ids=None, chapter=None, highlights=None, qid=None):
        self.qid = qid
        self.verses = []
        self.this_legend = legend_tpl.format(base_doc=base_doc)
        verse_ids_str = ','.join((str(v) for v in verse_ids)) if verse_ids != None else None
        cfield = 'verse.id'
        cwfield = 'word_verse.verse_id'
        condition_pre = 'WHERE {{}} IN ({})'.format(verse_ids_str) if verse_ids != None else 'WHERE chapter_id = {}'.format(chapter) if chapter != None else ''
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)
        self.hl_query = json.dumps(highlights if highlights != None else [])
        
        self.view_state = {}
        for (tg, init) in toggles:
            vstate = request.vars[tg]
            vstate = None if vstate == None else vstate.lower() == 'true' or vstate == '1' or vstate == 'on'
            if vstate == None:
                cvstate = None
                if request.cookies.has_key(tg):
                    cvstate = request.cookies[tg].value
                else:
                    cvstate = None
                vstate = init if cvstate == None else cvstate == 'True'
            response.cookies[tg] = vstate
            response.cookies[tg]['expires'] = 30 * 24 * 3600
            response.cookies[tg]['path'] = '/'
            self.view_state[tg] = vstate

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

    def legend(self, request, response, extra=None):
        return '''
<div class="sel">
    <a href="#" id="qhloff">highlights off</a>
    <span id="curviewlnk">{viewlink}</span>
    <input type="checkbox" id="toggle_txt_p" name="toggle_txt_p"/>text -
    <input type="checkbox" id="toggle_txt_il" name="toggle_txt_il"/>data {extra}
</div>
<script type="text/javascript">set_highlights_off()</script>
<div class="txt_il">{legend}</div>'''.format(legend=self.this_legend, viewlink=viewlink(request, response), extra='' if extra == None else extra)

    def adjust_data_view(self):
        adjustments = ['set_{}({})\n'.format(tg, 'true' if self.view_state[tg] else 'false') for tg in self.view_state]
        return '\n'.join(adjustments)


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

