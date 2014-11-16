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

data_spec = '''
ht,1 hl,1 tt,0 tl,0 gl,1 wd1,1 wd1_subpos,0 wd1_pos,1 wd1_lang,0 wd1_n,0 wd2,1 wd2_gender,1 wd2_gnumber,1 wd2_person,1 wd2_state,1 wd2_tense,1 wd2_stem,1 sp,1 sp_rela,1 sp_n,1 ph,1 ph_det,1 ph_fun,1 ph_typ,1 ph_n,1 cl,1 cl_dom,1 cl_typ,1 cl_n,1 sn,1 sn_n,1 txt_p,1 txt_il,0
'''.strip().split()
data_proto = [tuple(d.split(',')) for d in data_spec]
datas = [(x[0], x[1] == '1') for x in data_proto]

qview_spec = '''qhloff,0 qhlone,0 qhlmy,0 qhlmany,1'''.strip().split()
qview_proto = [tuple(q.split(',')) for q in qview_spec]
qviews = [(x[0], x[1] == '1') for x in qview_proto]

qcol_spec = '''sel_one,yellow'''.strip().split()
qcols = [tuple(q.split(',')) for q in qcol_spec]

class Queries():
    qcolor_spec = '''#ff0000,red,1 #ff6688,salmon,1 #ffcc66,orange,1 #ffff00,yellow,1 #00ff00,green,1 #ccff66,spring,1 #66ffcc,tropical,1 #00ffff,turquoise,1 #8888ff,blue,1 #66ccff,skye,1 #cc44ff,lilac,1 #ff00ff,magenta,1 #eeeeee,grey,0 #aaaaaa,gray,0 #000000,black,0 #ffffff,white,0'''.strip().split()
    qcolor_proto = [tuple(qc.split(',')) for qc in qcolor_spec]
    qcolors = [x[0] for x in qcolor_proto]
    qcolornames = dict((x[0], x[1]) for x in qcolor_proto)
    qcolorcodes = dict((x[1], x[0]) for x in qcolor_proto)
    qdefaultcolors = [x[0] for x in qcolor_proto if x[2] == '1']
    nrows = 4
    ncols = 4
    dnrows = 3
    dncols = 4
    ndefcolors = len(qdefaultcolors)

    def __init__(self, page_kind, request, response):
        if Queries.nrows * Queries.ncols != len(Queries.qcolors):
            print("Query settings: mismatch in number of colors: {} * {} != {}".format(Queries.nrows, Queries.ncols, len(Queries.qcolors)))
        if Queries.dnrows * Queries.dncols != len(Queries.qdefaultcolors):
            print("Query settings: mismatch in number of default colors: {} * {} != {}".format(Queries.dnrows, Queries.dncols, len(Queries.qdefaultcolors)))
        init_qview = [x[0] for x in qviews if x[1]]
        if len(init_qview) != 1:
            print("Query settings: the initial query view state is not uniquely defined: {}".format(init_qview))
            self.init_qview = qviews[-1][0]
        else:
            self.init_qview = init_qview[0]

        self.page_kind = page_kind
        self.data_view = {}
        self.query_view = {}
        self.query_map = {}
        cdata_view = {}
        cquery_view = {}
        cquery_map = {}
        if request.cookies.has_key('dataview'):
            cdata_view = json.loads(request.cookies['dataview'].value) 
        if request.cookies.has_key('querymap'):
            cquery_map = json.loads(request.cookies['querymap'].value) 
        if page_kind == 'passage' and request.cookies.has_key('queryview'):
            cquery_view = json.loads(request.cookies['queryview'].value) 
        for (x, init) in datas:
            vstate = request.vars[x]
            vstate = None if vstate == None else vstate == '1'
            if vstate == None:
                cvstate = cdata_view.get(x, None) 
                vstate = init if cvstate == None else cvstate == 1
            else:
                cdata_view[x] = 1 if vstate else 0
            self.data_view[x] = vstate
        if page_kind == 'passage':
            for (x, init) in qviews:
                vstate = request.vars[x]
                vstate = None if vstate == None else vstate == '1'
                if vstate == None:
                    cvstate = cquery_view.get(x, None) 
                    vstate = init if cvstate == None else cvstate == 1
                else:
                    cquery_view[x] = 1 if vstate else 0
                self.query_view[x] = vstate
            for (x, init) in qcols:
                vstate = request.vars[x]
                if vstate == None:
                    cvstate = cquery_view.get(x, None) 
                    vstate = init if cvstate == None else cvstate
                else:
                    cquery_view[x] = vstate
                self.query_view[x] = vstate
        for x in cquery_map: self.query_map[x] = cquery_map[x]
        for x in request.vars:
            if x[0] == 'q' and x[1:].isdigit():
                self.query_map[x[1:]] = request.vars[x]

        response.cookies['dataview'] = json.dumps(cdata_view)
        response.cookies['dataview']['expires'] = 30 * 24 * 3600
        response.cookies['dataview']['path'] = '/'
        if page_kind == 'passage':
            response.cookies['queryview'] = json.dumps(cquery_view)
            response.cookies['queryview']['expires'] = 30 * 24 * 3600
            response.cookies['queryview']['path'] = '/'
        response.cookies['querymap'] = json.dumps(self.query_map)
        response.cookies['querymap']['expires'] = 30 * 24 * 3600
        response.cookies['querymap']['path'] = '/'

    def adjust_view(self):
        adjustments = ['set_d("{}", {})\n'.format(x[0], 'true' if self.data_view[x[0]] else 'false') for x in datas]
        if self.page_kind == 'passage':
            qviewon = [x[0] for x in qviews if self.query_view[x[0]]]
            thisison = qviewon[0] if len(qviewon) else self.init_qview 
            adjustments.extend(['colorinit2("{}","{}","{}")\n'.format(thisison, self.query_view[x[0]], Queries.qcolorcodes[self.query_view[x[0]]]) for x in qcols])
        if self.page_kind == 'passage':
            adjustments.append('''$('#cviewlink').val(view_url + getqueryviewvars(false))''')
        else:
            adjustments.append('''$('#cviewlink').val(view_url + getdataviewvars(false))''')
        return '\n'.join(adjustments)

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
    def _qsel(qid, initn): return '<table class="picked"><tr><td class="cc_sel" id="sel_{qid}" prop="{n}">&nbsp;</td></tr></table>\n'.format(qid=qid, n=initn)

    def _js(self, qid, initc, monads):
        return 'jscolorpicker({qid}, "{ic}", {mn})\n'.format(qid=qid, ic=initc, mn='null' if monads == None else "'{}'".format(monads))

    def _js2(self):
        return 'jscolorpicker2()\n'

    def colorpicker(self, qid, monads=None):
        initn = self.query_map.get(str(qid), None)
        initc = Queries.qcolorcodes.get(initn, Queries._qdef(qid))
        initn = Queries.qcolornames[initc]
        return '{s}{p}<script type="text/javascript">{j}</script>\n'.format(s=Queries._qsel(qid, initn), p=Queries._ctable(qid), j=self._js(qid, initc, monads))

    def colorpicker2(self):
        return '{s}{p}<script type="text/javascript">{j}</script>\n'.format(s=Queries._qsel('one', 'choose...'), p=Queries._ctable('one'), j=self._js2())

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

def adapted_text(text, user_agent): return '' if text == '' else (text + ('&nbsp;' if ord(text[-1]) in replace_set else '')) if user_agent == 'Chrome' else text

def h_esc(material, fill=True):
    material = material.replace(
        '&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot').replace(
        "'", '&apos;').replace('\\n', '\n')
    if fill:
        if material == '': material = '&nbsp;'
    return material

class Verses():
    def __init__(self, passage_db, page_kind, verse_ids=None, chapter=None, highlights=None, qid=None):
        self.qid = qid
        self.page_kind = page_kind
        self.verses = []
        self.this_legend = legend_tpl.format(base_doc=base_doc)
        verse_ids_str = ','.join((str(v) for v in verse_ids)) if verse_ids != None else None
        cfield = 'verse.id'
        cwfield = 'word_verse.verse_id'
        condition_pre = 'WHERE {{}} IN ({})'.format(verse_ids_str) if verse_ids != None else 'WHERE chapter_id = {}'.format(chapter) if chapter != None else ''
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)
        self.hl_query = json.dumps(highlights if highlights != None else [])

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

    def legend(self): return self.this_legend

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

