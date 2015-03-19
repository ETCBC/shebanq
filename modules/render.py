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

ccolor_spec = '''
     0,z0
     1,z1
     2,z2
     5,z3
    10,z4
    20,z5
    50,z6
    51,z7
'''

vcolor_spec = '''
    red,#ff0000,#ff0000,1 salmon,#ff6688,#ee7799,1 orange,#ffcc66,#eebb55,1 yellow,#ffff00,#dddd00,1
    green,#00ff00,#00bb00,1 spring,#ddff77,#77dd44,1 tropical,#66ffcc,#55ddbb,1 turquoise,#00ffff,#00eeee,1
    blue,#8888ff,#0000ff,1 skye,#66ccff,#55bbff,1 lilac,#cc88ff,#aa22ff,1 magenta,#ff00ff,#ee00ee,1
    grey,#eeeeee,#eeeeee,0 gray,#aaaaaa,#aaaaaa,0 black,#000000,#000000,0 white,#ffffff,#ffffff,0
'''

vcolor_proto = [tuple(vc.split(',')) for vc in vcolor_spec.strip().split()]
vdefaultcolors = [x[0] for x in vcolor_proto if x[3] == '1']
vcolornames = [x[0] for x in vcolor_proto]
vcolors = dict((x[0], dict(q=x[1], w=x[2])) for x in vcolor_proto)
ndefcolors = len(vdefaultcolors)

field_names = '''
    word_heb word_vlex word_clex word_tran word_lex word_glex word_gloss
    word_subpos word_pos word_lang word_number
    word_gender word_gnumber word_person word_state word_tense word_stem
    word_nme word_pfm word_prs word_uvf word_vbe word_vbs
    subphrase_border subphrase_number subphrase_rela
    phrase_border phrase_number phrase_atom_number phrase_rela phrase_atom_rela phrase_function phrase_typ phrase_det
    clause_border clause_number clause_atom_number clause_atom_code clause_atom_tab clause_rela clause_typ clause_txt
    sentence_border sentence_number sentence_atom_number
'''.strip().split()

hebrewdata_lines_spec = '''
    ht:ht=word_heb=text-h
    hl:hl_hlv=word_vlex=lexeme-v,hl_hlc=word_clex=lexeme-c
    tt:tt=word_tran=text-t
    tl:tl_tlv=word_glex=lexeme-g,tl_tlc=word_lex=lexeme-t
    gl:gl=word_gloss=gloss
    wd1:wd1_subpos=word_subpos=lexical_set,wd1_pos=word_pos=part-of-speech,wd1_lang=word_lang=language,wd1_n=word_number=monad
    wd2:wd2_gender=word_gender=gender,wd2_gnumber=word_gnumber=number,wd2_person=word_person=person,wd2_state=word_state=state,wd2_tense=word_tense=tense,wd2_stem=word_stem=verbal_stem
    wd3:wd3_nme=word_nme=nme,wd3_pfm=word_pfm=pfm,wd3_prs=word_prs=prs,wd3_uvf=word_uvf=uvf,wd3_vbe=word_vbe=vbe,wd3_vbs=word_vbs=vbs
    sp:sp_rela=subphrase_rela=rela,sp_n=subphrase_number=subphrase#
    ph:ph_det=phrase_det=determination,ph_fun=phrase_function=function,ph_typ=phrase_typ=type-ph,ph_rela=phrase_rela=rela,ph_arela=phrase_atom_rela=rela_a,ph_an=phrase_atom_number=phrase_a#,ph_n=phrase_number=phrase#
    cl:cl_txt=clause_txt=txt,cl_typ=clause_typ=type-cl,cl_rela=clause_rela=rela,cl_tab=clause_atom_tab=tab,cl_code=clause_atom_code=code,cl_an=clause_atom_number=clause_a#,cl_n=clause_number=clause#
    sn:sn_an=sentence_atom_number=sentence_a#,sn_n=sentence_number=sentence#
'''.strip().split()
hebrewdata_lines = []
for item in hebrewdata_lines_spec:
    (line, fieldspec) = item.split(':')
    fields = [x.split('=') for x in fieldspec.split(',')]
    hebrewdata_lines.append((line, tuple(fields)))

specs = dict(
    material=(
        '''version book chapter iid page mr qw tp''',
        '''alnum:10 alnum:30 int:1-150 int:1-1000000 int:1-1000000 enum:m,r enum:q,w enum:txt_p,txt_il''',
        {'': '''4 Genesis 1 -1 1 m q txt_p'''},
    ),
    hebrewdata=('''
        ht
        hl hl_hlv hl_hlc
        tt
        tl tl_tlv tl_tlc
        gl
        wd1 wd1_subpos wd1_pos wd1_lang wd1_n
        wd2 wd2_gender wd2_gnumber wd2_person wd2_state wd2_tense wd2_stem
        wd3 wd3_nme wd3_pfm wd3_prs wd3_uvf wd3_vbe wd3_vbs
        sp sp_rela sp_n
        ph ph_det ph_fun ph_typ ph_rela ph_arela ph_an ph_n
        cl cl_txt cl_typ cl_rela cl_tab cl_code cl_an cl_n
        sn sn_an sn_n
    ''','''
        bool
        bool bool bool
        bool
        bool bool bool
        bool
        bool bool bool bool bool
        bool bool bool bool bool bool bool
        bool bool bool bool bool bool bool
        bool bool bool
        bool bool bool bool bool bool bool bool
        bool bool bool bool bool bool bool bool
        bool bool bool
    ''', {'': '''
        v
        v x v
        x
        x x v
        v
        v x v x x
        v v v v v v v
        x x x v x v x
        v v v
        v v v x x v v v
        v v v v v v v v
        v v v
    '''}),
    highlights=(
        '''get active sel_one''',
        '''bool enum:hloff,hlone,hlcustom,hlmany enum:color''',
        dict(q='x hlcustom grey', w='x hlcustom gray'),
    ),
    colormap=(
        '0',
        '''enum:color''',
        dict(q='white', w='black'),
    ),
    rest=(
        '''pref lan letter''',
        '''alnum:30 enum:hbo,arc int:1-100000''',
        {'': '''my hbo 1488'''},
    )
)

style = dict(
    q=dict(prop='background-color', default='grey', off='white', subtract=250, T='Q', t='q', Tag='Query', tag='query', Tags='Queries', tags='queries'),
    w=dict(prop='color', default='gray', off='black', subtract=250, T='W', t='w', Tag='Word', tag='word', Tags='Words', tags='words'),
    m=dict(subtract=250, T='I', t='i', Tag='Item', tag='item', Tags='Items', tags='items'),
)

legend_tpl = '''
<table id="legend" class="il">
    <tr class="il l_ht">
        <td class="c l_ht"><input type="checkbox" id="ht" name="ht"/></td>
        <td class="il l_ht"><a target="_blank" href="{base_doc}/g_word_utf8.html"><span class="l_ht">text דְּבַ֥ר</span></a></td>
    </tr>

    <tr class="il l_hl">
        <td class="c l_hl"><input type="checkbox" id="hl" name="hl"/></td>
        <td class="il l_hl">
            <span class="il l_hl_hlv">lexeme</span>&nbsp;&nbsp;
            <input type="checkbox" id="hl_hlv" name="hl_hlv"/>
                <a target="_blank" href="{base_doc}/vocalized_lexeme.html"><span class="il l_hl_hlv">דָּבָר</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="hl_hlc" name="hl_hlc"/>
                <a target="_blank" href="{base_doc}/lex_utf8.html"><span class="il l_hl_hlc">דבר/</span></a>
        </td>
    </tr>

    <tr class="il l_tt">
        <td class="c l_tt"><input type="checkbox" id="tt" name="tt"/></td>
        <td class="il l_tt"><a target="_blank" href="{base_doc}/g_word.html"><span class="l_tt">text</span></a></td>
    </tr>

    <tr class="il l_tl">
        <td class="c l_tl"><input type="checkbox" id="tl" name="tl"/></td>
        <td class="il l_tl">
            <input type="checkbox" id="tl_tlv" name="tl_tlv"/>
                <a target="_blank" href="{base_doc}/g_lex.html"><span class="il l_tl_tlv">lexeme-v</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="tl_tlc" name="tl_tlc"/>
                <a target="_blank" href="{base_doc}/lex.html"><span class="il l_tl_tlc">lexeme-c</span></a>
        </td>
    </tr>

    <tr class="il l_gl">
        <td class="c l_gl"><input type="checkbox" id="gl" name="gl"/></td>
        <td class="il l_gl"><a target="_blank" href="{base_doc}/gloss.html"><span class="l_gl">gloss</span></a></td>
    </tr>

    <tr class="il l_wd1">
        <td class="c l_wd1"><input type="checkbox" id="wd1" name="wd1"/></td>
        <td class="il l_wd1">
            <input type="checkbox" id="wd1_subpos" name="wd1_subpos"/>
                <a target="_blank" href="{base_doc}/ls.html"><span class="il l_wd1_subpos">lexical set</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_pos" name="wd1_pos"/>
                <a target="_blank" href="{base_doc}/sp.html"><span class="il l_wd1_pos">part-of-speech</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_lang" name="wd1_lang"/>
                <a target="_blank" href="{base_doc}/language.html"><span class="il l_wd1_lang">language</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_n" name="wd1_n"/>
                <a target="_blank" href="{base_doc}/monads.html"><span class="n l_wd1_n">monad#</span></a>
        </td>
    </tr>

    <tr class="il l_wd2">
        <td class="c l_wd2"><input type="checkbox" id="wd2" name="wd2"/></td>
        <td class="il l_wd2">
            <input type="checkbox" id="wd2_gender" name="wd2_gender"/>
                <a target="_blank" href="{base_doc}/gn.html"><span class="il l_wd2_gender">gender</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_gnumber" name="wd2_gnumber"/>
                <a target="_blank" href="{base_doc}/nu.html"><span class="il l_wd2_gnumber">number</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_person" name="wd2_person"/>
                <a target="_blank" href="{base_doc}/ps.html"><span class="il l_wd2_person">person</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_state" name="wd2_state"/>
                <a target="_blank" href="{base_doc}/st.html"><span class="il l_wd2_state">state</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_tense" name="wd2_tense"/>
                <a target="_blank" href="{base_doc}/vt.html"><span class="il l_wd2_tense">tense</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_stem" name="wd2_stem"/>
                <a target="_blank" href="{base_doc}/vs.html"><span class="il l_wd2_stem">verbal stem</span></a>
        </td>
    </tr>

    <tr class="il l_wd3">
        <td class="c l_wd3"><input type="checkbox" id="wd3" name="wd3"/></td>
        <td class="il l_wd3">
            <input type="checkbox" id="wd3_nme" name="wd3_nme"/>
                <a target="_blank" href="{base_doc}/nme.html"><span class="il l_wd3_nme">nme</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_pfm" name="wd3_pfm"/>
                <a target="_blank" href="{base_doc}/pfm.html"><span class="il l_wd3_pfm">pfm</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_prs" name="wd3_prs"/>
                <a target="_blank" href="{base_doc}/prs.html"><span class="il l_wd3_prs">prs</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_uvf" name="wd3_uvf"/>
                <a target="_blank" href="{base_doc}/uvf.html"><span class="il l_wd3_uvf">uvf</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_vbe" name="wd3_vbe"/>
                <a target="_blank" href="{base_doc}/vbe.html"><span class="il l_wd3_vbe">vbe</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_vbs" name="wd3_vbs"/>
                <a target="_blank" href="{base_doc}/vbs.html"><span class="il l_wd3_vbs">vbs</span></a>
        </td>
    </tr>

    <tr class="il l_sp">
        <td class="c l_sp"><input type="checkbox" id="sp" name="sp"/></td>
        <td class="il l_sp">
            <input type="checkbox" id="sp_rela" name="sp_rela"/>
                <a target="_blank" href="{base_doc}/rela.html"><span class="il l_sp_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="sp_n" name="sp_n"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n l_sp_n">subphrase#</span></a>
        </td>
    </tr>

    <tr class="il l_ph">
        <td class="c l_ph"><input type="checkbox" id="ph" name="ph"/></td>
        <td class="il l_ph">
            <input type="checkbox" id="ph_det" name="ph_det"/>
                <a target="_blank" href="{base_doc}/det.html"><span class="il l_ph_det">determination</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_fun" name="ph_fun"/>
                <a target="_blank" href="{base_doc}/function.html"><span class="il l_ph_fun">function</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_typ" name="ph_typ"/>
                <a target="_blank" href="{base_doc}/typ.html"><span class="il l_ph_typ">type</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_rela" name="ph_rela"/>
                <a target="_blank" href="{base_doc}/rela.html"><span class="il l_ph_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_arela" name="ph_arela"/>
                <a target="_blank" href="{base_doc}/rela.html"><span class="a il l_ph_arela">rela_a</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_an" name="ph_an"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n a il l_ph_an">phrase_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_n" name="ph_n"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n l_ph_n">phrase#</span></a>
        </td>
    </tr>

    <tr class="il l_cl">
        <td class="c l_cl"><input type="checkbox" id="cl" name="cl"/></td>
        <td class="il l_cl">
            <input type="checkbox" id="cl_txt" name="cl_txt"/>
                <a target="_blank" href="{base_doc}/txt.html"><span class="il l_cl_txt">txt</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_typ" name="cl_typ"/>
                <a target="_blank" href="{base_doc}/typ.html"><span class="il l_cl_typ">type</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_rela" name="cl_rela"/>
                <a target="_blank" href="{base_doc}/rela.html"><span class="il l_cl_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_tab" name="cl_tab"/>
                <a target="_blank" href="{base_doc}/tab.html"><span class="il a l_cl_tab">tab</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_code" name="cl_code"/>
                <a target="_blank" href="{base_doc}/code.html"><span class="il a l_cl_code">code</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_an" name="cl_an"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n a il l_cl_an">clause_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_n" name="cl_n"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n l_cl_n">clause#</span></a>
        </td>
    </tr>

    <tr class="il l_sn">
        <td class="c l_sn"><input type="checkbox" id="sn" name="sn"/></td>
        <td class="il l_sn">
            <input type="checkbox" id="sn_an" name="sn_an"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n a il l_sn_an">sentence_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="sn_n" name="sn_n"/>
                <a target="_blank" href="{base_doc}/number.html"><span class="n l_sn_n">sentence#</span></a>
        </td>
    </tr>
</table>
'''

text_tpl = u'''<table class="il c">
    <tr class="il ht">
        <td class="il ht"><span m="{word_number}" class="ht">{word_heb}</span></td>
    </tr>
    <tr class="il hl">
        <td class="il hl"><span l="{lexicon_id}" class="il hl_hlv">{word_vlex}</span>&nbsp;&nbsp;<span l="{lexicon_id}" class="il hl_hlc">{word_clex}</span></td>
    </tr>
    <tr class="il tt">
        <td class="il tt"><span m="{word_number}" class="tt">{word_tran}</span></td>
    </tr>
    <tr class="il tl">
        <td class="il tl"><span l="{lexicon_id}" class="tl tl_tlv">{word_glex}</span>&nbsp;&nbsp;<span l="{lexicon_id}" class="il tl_tlc">{word_lex}</span></td>
    </tr>
    <tr class="il gl">
        <td class="il gl"><span class="gl">{word_gloss}</span></td>
    </tr>
    <tr class="il wd1">
        <td class="il wd1"><span class="il wd1_subpos">{word_subpos}</span>&nbsp;<span class="il wd1_pos">{word_pos}</span>&nbsp;<span class="il wd1_lang">{word_lang}</span>&nbsp;<span class="n wd1_n">{word_number}</span></td>
    </tr>
    <tr class="il wd2">
        <td class="il wd2"><span class="il wd2_gender">{word_gender}</span>&nbsp;<span class="il wd2_gnumber">{word_gnumber}</span>&nbsp;<span class="il wd2_person">{word_person}</span>&nbsp;<span class="il wd2_state">{word_state}</span>&nbsp;<span class="il wd2_tense">{word_tense}</span>&nbsp;<span class="il wd2_stem">{word_stem}</span></td>
    </tr>
    <tr class="il wd3">
        <td class="il wd3"><span class="il wd3_nme">{word_nme}</span>&nbsp;<span class="il wd3_pfm">{word_pfm}</span>&nbsp;<span class="il wd3_prs">{word_prs}</span>&nbsp;<span class="il wd3_uvf">{word_uvf}</span>&nbsp;<span class="il wd3_vbe">{word_vbe}</span>&nbsp;<span class="il wd3_vbs">{word_vbs}</span></td>
    </tr>
    <tr class="il sp">
        <td class="il sp {subphrase_border}"><span class="il sp_rela">{subphrase_rela}</span>&nbsp;<span class="n sp_n">{subphrase_number}</span></td>
    </tr>
    <tr class="il ph">
        <td class="il ph {phrase_border}"><span class="il ph_det">{phrase_det}</span>&nbsp;<span class="il ph_fun">{phrase_function}</span>&nbsp;<span class="il ph_typ">{phrase_typ}</span>&nbsp;<span class="il ph_rela">{phrase_rela}</span>&nbsp;<span class="a il ph_arela">{phrase_atom_rela}</span>&nbsp;<span class="n a ph_an">{phrase_atom_number}</span>&nbsp;<span class="n ph_n">{phrase_number}</span></td>
    </tr>
    <tr class="il cl">
        <td class="il cl {clause_border}"><span class="il cl_txt">{clause_txt}</span>&nbsp;<span class="il cl_typ">{clause_typ}</span>&nbsp;<span class="il cl_rela">{clause_rela}</span>&nbsp;<span class="a cl_tab">{clause_atom_tab}</span>&nbsp;<span class="a cl_code">{clause_atom_code}</span>&nbsp;<span class="n a cl_an">{clause_atom_number}</span>&nbsp;<span class="n cl_n">{clause_number}</span></td>
    </tr>
    <tr class="il sn">
        <td class="il sn {sentence_border}"><span class="n a sn_an">{sentence_atom_number}</span>&nbsp;<span class="n sn_n">{sentence_number}</span></td>
    </tr>
</table>'''

def vcompile(tp):
    if tp == 'bool':
        return lambda d, x: x if x in {'x', 'v'} else d
    (t, v) = tp.split(':')
    if t == 'alnum':
        return lambda d, x: x if x != None and len(x) < int(v) and x.replace('_','').replace(' ','').isalnum() else d
    elif t == 'int':
        (lowest, highest) = v.split('-')
        return lambda d, x: int(x) if x != None and str(x).isdigit() and int(x) >= int(lowest) and int(x) <= int(highest) else int(d) if d != None else d
    elif t == 'enum':
        vals = set(vcolors.keys()) if v == 'color' else set(v.split(','))
        return lambda d, x: x if x != None and x in vals else d 

settings = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
validation = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))

for group in specs:
    (flds, types, init) = specs[group]
    flds = flds.strip().split()
    types = types.strip().split()
    valtype = [vcompile(tp) for tp in types]
    for qw in init:
        initk = init[qw].strip().split()
        for (i, f) in enumerate(flds):
            settings[group][qw][f] = initk[i]
            validation[group][qw][f] = valtype[i]

def get_request_val(group, qw, f, default=True):
    rvar = qw+f
    if rvar == 'iid':
        x = current.request.vars.id or current.request.vars.iid
    else:
        x = current.request.vars.get(rvar, None)
    fref = '0' if group == 'colormap' else f
    d = settings[group][qw][fref] if default else None
    return validation[group][qw][fref](d, x)

def make_ccolors():
    ccolor_proto = [tuple(cc.split(',')) for cc in ccolor_spec.strip().split()]
    ccolors = []
    prevl = 0 
    for (l,z) in ccolor_proto:
        newl = int(l) + 1
        for i in range(prevl, newl):
            ccolors.append(z)
        prevl = newl 
    return ccolors

if nrows * ncols != len(vcolornames):
    print("View settings: mismatch in number of colors: {} * {} != {}".format(nrows, ncols, len(vcolornames)))
if dnrows * dncols != len(vdefaultcolors):
    print("View settings: mismatch in number of default colors: {} * {} != {}".format(dnrows, dncols, len(vdefaultcolors)))

def ccell(qw,iid,c): return '\t\t<td class="c{qw} {qw}{iid}"><a href="#">{n}</a></td>'.format(qw=qw,iid=iid,n=vcolornames[c])
def crow(qw,iid,r): return '\t<tr>\n{}\n\t</tr>'.format('\n'.join(ccell(qw,iid,c) for c in range(r * ncols, (r + 1) * ncols)))
def ctable(qw, iid): return '<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'.format(qw=qw,iid=iid, cs='\n'.join(crow(qw,iid,r) for r in range(nrows)))

def vsel(qw, iid, typ):
    content = '&nbsp;' if qw == 'q' else 'w'
    selc = '' if typ else '<span class="pickedc cc_selc_{qw}"><input type="checkbox" id="selc_{qw}{iid}" name="selc_{qw}{iid}"/></span>&nbsp;'
    sel = '<span class="picked cc_sel_{qw}" id="sel_{qw}{iid}"><a href="#">{lab}</a></span>'
    return (selc + sel).format (qw=qw,iid=iid, lab=content)

def legend(): return legend_tpl.format(base_doc=base_doc)
def colorpicker(qw, iid, typ): return '{s}{p}\n'.format(s=vsel(qw, iid, typ), p=ctable(qw, iid))

def get_fields():
    if get_request_val('material', '', 'tp') == 'txt_p':
        hfields = [('word_number', 'monad'), ('word_heb', 'text')]
    else:
        hfields = []
        for (line, fields) in hebrewdata_lines:
            if get_request_val('hebrewdata', '', line) == 'v':
                for (f, name, pretty_name) in fields:
                    if get_request_val('hebrewdata', '', f) == 'v':
                        hfields.append((name, pretty_name))
    return hfields
    
class Viewsettings():
    def __init__(self):
        self.state = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
        self.pref = get_request_val('rest', '', 'pref')
        for group in settings:
            self.state[group] = {}
            for qw in settings[group]:
                self.state[group][qw] = {}
                from_cookie = {}
                if current.request.cookies.has_key(self.pref+group+qw):
                    if self.pref == 'my':
                        try:
                            from_cookie = json.loads(urllib.unquote(current.request.cookies[self.pref+group+qw].value))
                        except ValueError: pass
                if group == 'colormap':
                    for fid in from_cookie:
                        if len(fid) <= 7 and fid.isdigit():
                            vstate = validation[group][qw]['0'](None, from_cookie[fid])
                        if vstate != None:
                            self.state[group][qw][fid] = vstate
                    for f in current.request.vars:
                        fid = f[1:]
                        if len(fid) <= 7 and fid.isdigit():
                            vstate = get_request_val(group, qw, f, default=False)
                            if vstate != None:
                                from_cookie[fid] = vstate
                                self.state[group][qw][fid] = vstate
                elif group != 'rest':
                    for f in settings[group][qw]:
                        init = settings[group][qw][f]
                        vstate = validation[group][qw][f](init, from_cookie.get(f, None))
                        vstater = get_request_val(group, qw, f, default=False)
                        if vstater != None: vstate = vstater
                        from_cookie[f] = vstate
                        self.state[group][qw][f] = vstate

                if group != 'rest':
                    current.response.cookies[self.pref+group+qw] = urllib.quote(json.dumps(from_cookie))
                    current.response.cookies[self.pref+group+qw]['expires'] = 30 * 24 * 3600
                    current.response.cookies[self.pref+group+qw]['path'] = '/'


    def dynamics(self):
        book_proto = get_request_val('material', '', 'book')
        return '''
var vcolors = {vcolors}
var ccolors = {ccolors}
var vdefaultcolors = {vdefaultcolors}
var dncols = {dncols}
var dnrows = {dnrows}
var viewinit = {initstate}
var style = {style}
var pref = {pref}
dynamics()
'''.format(
    vdefaultcolors=json.dumps(vdefaultcolors),
    initstate=json.dumps(self.state),
    vcolors = json.dumps(vcolors),
    ccolors = json.dumps(make_ccolors()),
    style = json.dumps(style),
    pref = '"{}"'.format(self.pref),
    dncols = dncols,
    dnrows = dnrows,
)

def adapted_text(text, user_agent): return '' if text == '' else (text + ('&nbsp;' if ord(text[-1]) in replace_set else '')) if user_agent == 'Chrome' else text

def h_esc(material, fill=True):
    material = material.replace(
        '&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot').replace(
        "'", '&apos;').replace('\\n', '\n')
    if fill:
        if material == '': material = '&nbsp;'
    return material

class Verses():
    def __init__(self, passage_dbs, vr, mr, verse_ids=None, chapter=None, tp=None):
        self.version = vr
        passage_db = passage_dbs[vr]
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
            self.verses.append(Verse(passage_dbs, vr, v[1], v[2], v[3], xml=xml, word_data=word_data[v_id], tp=tp, mr=mr)) 

class Verse():
    def __init__(self, passage_dbs, version, book_name, chapter_num, verse_num, xml=None, word_data=None, tp=None, mr=None):
        self.version = vr
        passage_db = passage_dbs[vr]
        self.tp = tp
        self.mr = mr
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        if xml == None:
            xml = ''
        if word_data == None:
            word_records = passage_db.executesql('''
SELECT {}, lexicon_id FROM word
INNER JOIN word_verse ON word_number = word_verse.anchor
INNER JOIN verse ON verse.id = word_verse.verse_id
INNER JOIN chapter ON verse.chapter_id = chapter.id
INNER JOIN book ON chapter.book_id = book.id
WHERE book.name = '{}' AND chapter.chapter_num = {} AND verse.verse_num = {}
ORDER BY word_number;
'''.format(','.join(field_names), book_name, chapter_num, verse_num), as_dict=True)
            word_data = []
            for record in word_records:
                word_data.append(dict((x,h_esc(unicode(y), not x.endswith('_border'))) for (x,y) in record.items()))
        self.xml = xml
        self.word_data = word_data
        self.words = []

    def to_string(self):
        return "{}\n{}".format(self.citation_ref(), self.text)

    def chapter_link(self):
        return (self.book_name, self.chapter_num)

    def label(self):
        return (self.book_name.replace('_', ' '), self.book_name, self.chapter_num, self.verse_num)

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

