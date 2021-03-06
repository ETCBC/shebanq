#!/usr/bin/env python

import collections
import json
import urllib
import re
from base64 import b64decode, b64encode
import xml.etree.ElementTree as ET

from gluon import current
from blang import booklangs, booknames


biblang = "Hebrew"

nrows = 4
ncols = 4
dnrows = 3
dncols = 4

ccolor_spec = """
     0,z0
     1,z1
     2,z2
     5,z3
    10,z4
    20,z5
    50,z6
    51,z7
"""

vcolor_spec = """
    red,#ff0000,#ff0000,1 salmon,#ff6688,#ee7799,1 orange,#ffcc66,#eebb55,1
    yellow,#ffff00,#dddd00,1 green,#00ff00,#00bb00,1 spring,#ddff77,#77dd44,1
    tropical,#66ffcc,#55ddbb,1 turquoise,#00ffff,#00eeee,1 blue,#8888ff,#0000ff,1
    skye,#66ccff,#55bbff,1 lilac,#cc88ff,#aa22ff,1 magenta,#ff00ff,#ee00ee,1
    grey,#eeeeee,#eeeeee,0 gray,#aaaaaa,#aaaaaa,0 black,#000000,#000000,0
    white,#ffffff,#ffffff,0
"""

vcolor_proto = [tuple(vc.split(",")) for vc in vcolor_spec.strip().split()]
vdefaultcolors = [x[0] for x in vcolor_proto if x[3] == "1"]
vcolornames = [x[0] for x in vcolor_proto]
vcolors = dict((x[0], dict(q=x[1], w=x[2])) for x in vcolor_proto)
ndefcolors = len(vdefaultcolors)

tab_info = dict(
    txt_tb1="Notes view",
    txt_tb2="Syntax view",
    txt_tb3="Abstract view",
)
tp_labels = dict(
    txt_p="text",
    txt_tb1="Notes",
    txt_tb2="Syntax",
    txt_tb3="Abstract",
    txt_il="data",
)
tr_info = ["hb", "ph"]
tr_labels = dict(
    hb="hebrew",
    ph="phonetic",
)

tab_views = len(tab_info)
# next_tp is a mapping from a text type to the next:
# it goes txt_p => txt_tb1 => txt_tb2 => ... => txt_p
next_tp = dict(
    (
        "txt_p" if i == 0 else "txt_tb{}".format(i),
        "txt_tb{}".format(i + 1) if i < tab_views else "txt_p",
    )
    for i in range(tab_views + 1)
)

tr_views = len(tr_info)
# next_tr is a mapping from a script type to the next: it goes hb => ph => hb
next_tr = dict((tr_info[i], tr_info[(i + 1) % 2]) for i in range(tr_views))

nt_statorder = "o*+?-!"
nt_statclass = {
    "o": "nt_info",
    "+": "nt_good",
    "-": "nt_error",
    "?": "nt_warning",
    "!": "nt_special",
    "*": "nt_note",
}
nt_statsym = {
    "o": "circle",
    "+": "check-circle",
    "-": "times-circle",
    "?": "exclamation-circle",
    "!": "info-circle",
    "*": "star",
}
nt_statnext = {}
for (i, x) in enumerate(nt_statorder):
    nt_statnext[x] = nt_statorder[(i + 1) % len(nt_statorder)]

field_names = dict(
    txt_il="""
        word_heb word_ktv word_phono word_vlex word_clex
        word_tran word_lex word_glex word_gloss
        word_nmtp word_subpos word_pos word_pdp word_lang word_number
        word_gender word_gnumber word_person word_state word_tense word_stem
        word_nme word_pfm word_prs word_uvf word_vbe word_vbs
        word_freq_lex word_rank_lex word_freq_occ word_rank_occ
        subphrase_border subphrase_number subphrase_rela
        phrase_border phrase_number phrase_atom_number
        phrase_rela phrase_atom_rela phrase_function phrase_typ phrase_det
        clause_border clause_number clause_atom_number
        clause_atom_code clause_atom_tab clause_atom_pargr
        clause_rela clause_typ clause_txt
        sentence_border sentence_number sentence_atom_number
        """.strip().split(),
    txt_p="""
        word_phono word_phono_sep
        """.strip().split(),
    txt_tb1="""
        word_heb word_ktv word_phono word_phono_sep word_number
        phrase_border phrase_number phrase_function
        sentence_number clause_number clause_atom_number
        clause_atom_tab clause_txt clause_typ
        """.strip().split(),
    txt_tb2="""
        word_heb word_ktv word_phono word_phono_sep word_number
        phrase_border phrase_function
        sentence_number clause_number clause_atom_number
        clause_atom_tab clause_atom_code clause_txt clause_typ
        """.strip().split(),
    txt_tb3="""
        word_heb word_ktv word_phono word_phono_sep word_number
        word_lex word_pos word_gender
        phrase_border
        sentence_number clause_number clause_atom_number clause_atom_tab
        """.strip().split(),
)
hfields = dict(
    txt_p=[
        ("word_number", "monad"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_phono", "phtext"),
        ("word_phono_sep", "phsep"),
    ],
    txt_tb1=[
        ("word_number", "monad"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_phono", "phtext"),
        ("word_phono_sep", "phsep"),
        ("phrase_number", "phrase#"),
        ("phrase_function", "function"),
        ("clause_txt", "txt"),
        ("clause_typ", "typ"),
        ("clause_atom_tab", "tab"),
    ],
    txt_tb2=[
        ("word_number", "monad"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_phono", "phtext"),
        ("word_phono_sep", "phsep"),
        ("phrase_number", "phrase#"),
        ("phrase_function", "function"),
        ("clause_txt", "txt"),
        ("clause_typ", "typ"),
        ("clause_atom_tab", "tab"),
        ("clause_atom_code", "code"),
    ],
    txt_tb3=[
        ("word_number", "monad"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_lex", "lexeme-t"),
        ("word_pos", "part-of-speech"),
        ("word_gender", "gender"),
        ("phrase_number", "phrase#"),
        ("clause_atom_tab", "tab"),
    ],
)

notfillfields = {"word_phono", "word_phono_sep"}

hebrewdata_lines_spec = """
    ht:ht_ht=word_heb=text-h,ht_hk=word_ktv=ketiv
    pt:pt=word_phono=text-p
    hl:hl_hlv=word_vlex=lexeme-v,hl_hlc=word_clex=lexeme-c
    tt:tt=word_tran=text-t
    tl:tl_tlv=word_glex=lexeme-g,tl_tlc=word_lex=lexeme-t
    gl:gl=word_gloss=gloss
    wd1:wd1_nmtp=word_nmtp=nametype,wd1_subpos=word_subpos=lexical_set,wd1_pos=word_pos=part-of-speech,wd1_pdp=word_pdp=phrase-dependent-part-of-speech,wd1_lang=word_lang=language,wd1_n=word_number=monad
    wd2:wd2_gender=word_gender=gender,wd2_gnumber=word_gnumber=number,wd2_person=word_person=person,wd2_state=word_state=state,wd2_tense=word_tense=tense,wd2_stem=word_stem=verbal_stem
    wd3:wd3_nme=word_nme=nme,wd3_pfm=word_pfm=pfm,wd3_prs=word_prs=prs,wd3_uvf=word_uvf=uvf,wd3_vbe=word_vbe=vbe,wd3_vbs=word_vbs=vbs
    wd4:wd4_statfl=word_freq_lex=freq-lex,wd4_statrl=word_rank_lex=rank-lex,wd4_statfo=word_freq_occ=freq-occ,wd4_statro=word_rank_occ=rank-occ
    sp:sp_rela=subphrase_rela=rela,sp_n=subphrase_number=subphrase#
    ph:ph_det=phrase_det=determination,ph_fun=phrase_function=function,ph_typ=phrase_typ=type-ph,ph_rela=phrase_rela=rela,ph_arela=phrase_atom_rela=rela_a,ph_an=phrase_atom_number=phrase_a#,ph_n=phrase_number=phrase#
    cl:cl_txt=clause_txt=txt,cl_typ=clause_typ=type-cl,cl_rela=clause_rela=rela,cl_tab=clause_atom_tab=tab,cl_par=clause_atom_pargr=par,cl_code=clause_atom_code=code,cl_an=clause_atom_number=clause_a#,cl_n=clause_number=clause#
    sn:sn_an=sentence_atom_number=sentence_a#,sn_n=sentence_number=sentence#
""".strip().split()
hebrewdata_lines = []
for item in hebrewdata_lines_spec:
    (line, fieldspec) = item.split(":")
    fields = [x.split("=") for x in fieldspec.split(",")]
    hebrewdata_lines.append((line, tuple(fields)))

# make a translation table from latin book names (the ETCBC ones)
# to the specific languages
booktrans = {}
for lng in booknames[biblang]:
    for (i, book) in enumerate(booknames[biblang][lng]):
        booktrans.setdefault(lng, {})[booknames[biblang]["la"][i]] = book

specs = dict(
    material=(
        """version book chapter verse iid page mr qw tp tr lang""",
        (
            """alnum:10 alnum:30 int:1-150 int:1-200 base64:1024 """
            """int:1-1000000 enum:m,r enum:q,w,n enum:txt_p,{},txt_il """
            """enum:{} enum:{}"""
        ).format(
            ",".join("txt_tb{}".format(t) for t in range(1, tab_views + 1)),
            ",".join(tr_labels),
            ",".join(sorted(booknames[biblang])),
        ),
        {"": """4 Genesis 1 1 None 1 x m txt_p hb en"""},
    ),
    hebrewdata=(
        """
        ht ht_ht ht_hk
        pt
        hl hl_hlv hl_hlc
        tt
        tl tl_tlv tl_tlc
        gl
        wd1 wd1_nmtp wd1_subpos wd1_pos wd1_pdp wd1_lang wd1_n
        wd2 wd2_gender wd2_gnumber wd2_person wd2_state wd2_tense wd2_stem
        wd3 wd3_nme wd3_pfm wd3_prs wd3_uvf wd3_vbe wd3_vbs
        wd4 wd4_statfl wd4_statrl wd4_statfo wd4_statro
        sp sp_rela sp_n
        ph ph_det ph_fun ph_typ ph_rela ph_arela ph_an ph_n
        cl cl_txt cl_typ cl_rela cl_tab cl_par cl_code cl_an cl_n
        sn sn_an sn_n
    """,
        """
        bool bool bool bool
        bool
        bool bool bool
        bool
        bool bool bool
        bool
        bool bool bool bool bool bool
        bool bool bool bool bool bool bool
        bool bool bool bool bool bool bool
        bool bool bool bool bool
        bool bool bool
        bool bool bool bool bool bool bool bool
        bool bool bool bool bool bool bool bool bool
        bool bool bool
    """,
        {
            "": """
        v v v v
        v
        v x v
        x
        x x v
        v
        v x v x x x
        v v v v v v v
        x x x v x v x
        v v v x x
        v v v
        v v v x x v v v
        v v v v v v v v v
        v v v
    """
        },
    ),
    highlights=(
        """get active sel_one pub""",
        """bool enum:hloff,hlone,hlcustom,hlmany enum:color bool""",
        dict(q="x hlcustom grey x", w="x hlcustom gray x", n="x hlcustom black v"),
    ),
    colormap=(
        "0",
        """enum:color""",
        dict(q="white", w="black"),
    ),
    rest=(
        """pref lan letter extra""",
        """alnum:30 enum:hbo,arc int:1-100000 alnum:64""",
        {"": """my hbo 1488 None"""},
    ),
)

style = dict(
    q=dict(
        prop="background-color",
        default="grey",
        off="white",
        subtract=250,
        T="Q",
        t="q",
        Tag="Query",
        tag="query",
        Tags="Queries",
        tags="queries",
    ),
    w=dict(
        prop="color",
        default="gray",
        off="black",
        subtract=250,
        T="W",
        t="w",
        Tag="Word",
        tag="word",
        Tags="Words",
        tags="words",
    ),
    n=dict(
        subtract=250, T="N", t="n", Tag="Note", tag="note", Tags="Notes", tags="notes"
    ),
    m=dict(
        subtract=250, T="I", t="i", Tag="Item", tag="item", Tags="Items", tags="items"
    ),
)

legend = """
<table id="legend" class="il">
    <tr class="il l_ht">
        <td class="c l_ht"><input type="checkbox" id="ht" name="ht"/></td>
        <td class="il l_ht">
            <span class="il l_ht_ht">text</span>&nbsp;&nbsp;
            <input type="checkbox" id="ht_ht" name="ht_ht"/>
                <a target="_blank" href="#" fname="g_word_utf8"
                ><span class="l_ht_ht">דְּבַ֥ר</span></a>&nbsp;(qere) &nbsp;
            <input type="checkbox" id="ht_hk" name="ht_hk"/>
                <a target="_blank" href="#" fname="ketiv"
                ><span class="l_ht_hk">כתב</span></a>&nbsp;(ketiv) &nbsp;
        </td>
    </tr>
    <tr class="il l_pt">
        <td class="c l_pt"><input type="checkbox" id="pt" name="pt"/></td>
        <td class="il l_pt"><a target="_blank" href="#" fname="phono"
        ><span class="l_pt">text dāvˈār</span></a></td>
    </tr>

    <tr class="il l_hl">
        <td class="c l_hl"><input type="checkbox" id="hl" name="hl"/></td>
        <td class="il l_hl">
            <span class="il l_hl_hlv">lexeme</span>&nbsp;&nbsp;
            <input type="checkbox" id="hl_hlv" name="hl_hlv"/>
                <a target="_blank" href="#" fname="vocalized_lexeme"
                ><span class="il l_hl_hlv">דָּבָר</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="hl_hlc" name="hl_hlc"/>
                <a target="_blank" href="#" fname="lex_utf8"
                ><span class="il l_hl_hlc">דבר/</span></a>
        </td>
    </tr>

    <tr class="il l_tt">
        <td class="c l_tt"><input type="checkbox" id="tt" name="tt"/></td>
        <td class="il l_tt"><a target="_blank" href="#" fname="g_word"
        ><span class="l_tt">text</span></a></td>
    </tr>

    <tr class="il l_tl">
        <td class="c l_tl"><input type="checkbox" id="tl" name="tl"/></td>
        <td class="il l_tl">
            <input type="checkbox" id="tl_tlv" name="tl_tlv"/>
                <a target="_blank" href="#" fname="g_lex"
                ><span class="il l_tl_tlv">lexeme-v</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="tl_tlc" name="tl_tlc"/>
                <a target="_blank" href="#" fname="lex"
                ><span class="il l_tl_tlc">lexeme-c</span></a>
        </td>
    </tr>

    <tr class="il l_gl">
        <td class="c l_gl"><input type="checkbox" id="gl" name="gl"/></td>
        <td class="il l_gl"><a target="_blank" href="#" fname="gloss"
        ><span class="l_gl">gloss</span></a></td>
    </tr>

    <tr class="il l_wd1">
        <td class="c l_wd1"><input type="checkbox" id="wd1" name="wd1"/></td>
        <td class="il l_wd1">
            <input type="checkbox" id="wd1_nmtp" name="wd1_nmtp"/>
                <a target="_blank" href="#" fname="nametype"
                ><span class="il l_wd1_nmtp">nametype</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_subpos" name="wd1_subpos"/>
                <a target="_blank" href="#" fname="ls"
                ><span class="il l_wd1_subpos">lexical set</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_pos" name="wd1_pos"/>
                <a target="_blank" href="#" fname="sp"
                ><span class="il l_wd1_pos">part-of-speech</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_pdp" name="wd1_pdp"/>
                <a target="_blank" href="#" fname="pdp"
                   title="phrase dependent part-of-speech"
                ><span class="il l_wd1_pdp">pdp</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_lang" name="wd1_lang"/>
                <a target="_blank" href="#" fname="language"
                ><span class="il l_wd1_lang">language</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd1_n" name="wd1_n"/>
                <a target="_blank" href="#" fname="monads"
                ><span class="n l_wd1_n">monad#</span></a>
        </td>
    </tr>

    <tr class="il l_wd2">
        <td class="c l_wd2"><input type="checkbox" id="wd2" name="wd2"/></td>
        <td class="il l_wd2">
            <input type="checkbox" id="wd2_gender" name="wd2_gender"/>
                <a target="_blank" href="#" fname="gn"
                ><span class="il l_wd2_gender">gender</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_gnumber" name="wd2_gnumber"/>
                <a target="_blank" href="#" fname="nu"
                ><span class="il l_wd2_gnumber">number</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_person" name="wd2_person"/>
                <a target="_blank" href="#" fname="ps"
                ><span class="il l_wd2_person">person</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_state" name="wd2_state"/>
                <a target="_blank" href="#" fname="st"
                ><span class="il l_wd2_state">state</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_tense" name="wd2_tense"/>
                <a target="_blank" href="#" fname="vt"
                ><span class="il l_wd2_tense">tense</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd2_stem" name="wd2_stem"/>
                <a target="_blank" href="#" fname="vs"
                ><span class="il l_wd2_stem">verbal stem</span></a>
        </td>
    </tr>

    <tr class="il l_wd3">
        <td class="c l_wd3"><input type="checkbox" id="wd3" name="wd3"/></td>
        <td class="il l_wd3">
            <input type="checkbox" id="wd3_nme" name="wd3_nme"/>
                <a target="_blank" href="#" fname="nme"
                ><span class="il l_wd3_nme">nme</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_pfm" name="wd3_pfm"/>
                <a target="_blank" href="#" fname="pfm"
                ><span class="il l_wd3_pfm">pfm</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_prs" name="wd3_prs"/>
                <a target="_blank" href="#" fname="prs"
                ><span class="il l_wd3_prs">prs</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_uvf" name="wd3_uvf"/>
                <a target="_blank" href="#" fname="uvf"
                ><span class="il l_wd3_uvf">uvf</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_vbe" name="wd3_vbe"/>
                <a target="_blank" href="#" fname="vbe"
                ><span class="il l_wd3_vbe">vbe</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd3_vbs" name="wd3_vbs"/>
                <a target="_blank" href="#" fname="vbs"
                ><span class="il l_wd3_vbs">vbs</span></a>
        </td>
    </tr>

    <tr class="il l_wd4">
        <td class="c l_wd4"><input type="checkbox" id="wd4" name="wd4"/></td>
        <td class="il l_wd4">
            <input type="checkbox" id="wd4_statfl" name="wd4_statfl"/>
                <a target="_blank" href="#" fname="freq_lex"
                ><span class="il l_wd4_statfl">freq(lex)</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd4_statrl" name="wd4_statrl"/>
                <a target="_blank" href="#" fname="rank_lex"
                ><span class="il l_wd4_statrl">rank(lex)</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd4_statfo" name="wd4_statfo"/>
                <a target="_blank" href="#" fname="freq_occ"
                ><span class="il l_wd4_statfo">freq(occ)</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="wd4_statro" name="wd4_statro"/>
                <a target="_blank" href="#" fname="rank_occ"
                ><span class="il l_wd4_statro">rank(occ)</span></a>&nbsp;&nbsp;
        </td>
    </tr>

    <tr class="il l_sp">
        <td class="c l_sp"><input type="checkbox" id="sp" name="sp"/></td>
        <td class="il l_sp">
            <input type="checkbox" id="sp_rela" name="sp_rela"/>
                <a target="_blank" href="#" fname="rela"
                ><span class="il l_sp_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="sp_n" name="sp_n"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n l_sp_n">subphrase#</span></a>
        </td>
    </tr>

    <tr class="il l_ph">
        <td class="c l_ph"><input type="checkbox" id="ph" name="ph"/></td>
        <td class="il l_ph">
            <input type="checkbox" id="ph_det" name="ph_det"/>
                <a target="_blank" href="#" fname="det"
                ><span class="il l_ph_det">determination</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_fun" name="ph_fun"/>
                <a target="_blank" href="#" fname="function"
                ><span class="il l_ph_fun">function</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_typ" name="ph_typ"/>
                <a target="_blank" href="#" fname="typ"
                ><span class="il l_ph_typ">type</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_rela" name="ph_rela"/>
                <a target="_blank" href="#" fname="rela"
                ><span class="il l_ph_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_arela" name="ph_arela"/>
                <a target="_blank" href="#" fname="rela"
                ><span class="a il l_ph_arela">rela_a</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_an" name="ph_an"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n a il l_ph_an">phrase_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="ph_n" name="ph_n"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n l_ph_n">phrase#</span></a>
        </td>
    </tr>

    <tr class="il l_cl">
        <td class="c l_cl"><input type="checkbox" id="cl" name="cl"/></td>
        <td class="il l_cl">
            <input type="checkbox" id="cl_txt" name="cl_txt"/>
                <a target="_blank" href="#" fname="txt"
                ><span class="il l_cl_txt">txt</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_typ" name="cl_typ"/>
                <a target="_blank" href="#" fname="typ"
                ><span class="il l_cl_typ">type</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_rela" name="cl_rela"/>
                <a target="_blank" href="#" fname="rela"
                ><span class="il l_cl_rela">rela</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_tab" name="cl_tab"/>
                <a target="_blank" href="#" fname="tab"
                ><span class="il a l_cl_tab">tab</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_par" name="cl_par"/>
                <a target="_blank" href="#" fname="pargr"
                ><span class="il a l_cl_par">pargr</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_code" name="cl_code"/>
                <a target="_blank" href="#" fname="code"
                ><span class="il a l_cl_code">code</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_an" name="cl_an"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n a il l_cl_an">clause_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="cl_n" name="cl_n"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n l_cl_n">clause#</span></a>
        </td>
    </tr>

    <tr class="il l_sn">
        <td class="c l_sn"><input type="checkbox" id="sn" name="sn"/></td>
        <td class="il l_sn">
            <input type="checkbox" id="sn_an" name="sn_an"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n a il l_sn_an">sentence_a#</span></a>&nbsp;&nbsp;
            <input type="checkbox" id="sn_n" name="sn_n"/>
                <a target="_blank" href="#" fname="number"
                ><span class="n l_sn_n">sentence#</span></a>
        </td>
    </tr>
</table>
""".replace(
    "\n", " "
)

text_tpl = """<table class="il c">
    <tr class="il ht">
        <td class="il ht"><span m="{word_number}" class="il ht_ht"
        >{word_heb}</span>&nbsp;&nbsp;<span class="il ht_hk">{word_ktv}</span></td>
    </tr>
    <tr class="il pt">
        <td class="il pt"><span m="{word_number}" class="pt">{word_phono}</span></td>
    </tr>
    <tr class="il hl">
        <td class="il hl"><span l="{lexicon_id}" class="il hl_hlv"
        >{word_vlex}</span>&nbsp;&nbsp;<span l="{lexicon_id}" class="il hl_hlc"
        >{word_clex}</span></td>
    </tr>
    <tr class="il tt">
        <td class="il tt"><span m="{word_number}" class="tt">{word_tran}</span></td>
    </tr>
    <tr class="il tl">
        <td class="il tl"><span l="{lexicon_id}" class="tl tl_tlv"
        >{word_glex}</span>&nbsp;&nbsp;<span l="{lexicon_id}" class="il tl_tlc"
        >{word_lex}</span></td>
    </tr>
    <tr class="il gl">
        <td class="il gl"><span class="gl">{word_gloss}</span></td>
    </tr>
    <tr class="il wd1">
        <td class="il wd1"><span class="il wd1_nmtp"
        >{word_nmtp}</span>&nbsp;<span class="il wd1_subpos"
        >{word_subpos}</span>&nbsp;<span class="il wd1_pos"
        >{word_pos}</span>&nbsp;<span class="il wd1_pdp"
        >{word_pdp}</span>&nbsp;<span class="il wd1_lang"
        >{word_lang}</span>&nbsp;<span class="n wd1_n"
        >{word_number}</span></td>
    </tr>
    <tr class="il wd2">
        <td class="il wd2"><span class="il wd2_gender"
        >{word_gender}</span>&nbsp;<span class="il wd2_gnumber"
        >{word_gnumber}</span>&nbsp;<span class="il wd2_person"
        >{word_person}</span>&nbsp;<span class="il wd2_state"
        >{word_state}</span>&nbsp;<span class="il wd2_tense"
        >{word_tense}</span>&nbsp;<span class="il wd2_stem"
        >{word_stem}</span></td>
    </tr>
    <tr class="il wd3">
        <td class="il wd3"><span class="il wd3_nme"
        >{word_nme}</span>&nbsp;<span class="il wd3_pfm"
        >{word_pfm}</span>&nbsp;<span class="il wd3_prs"
        >{word_prs}</span>&nbsp;<span class="il wd3_uvf"
        >{word_uvf}</span>&nbsp;<span class="il wd3_vbe"
        >{word_vbe}</span>&nbsp;<span class="il wd3_vbs"
        >{word_vbs}</span></td>
    </tr>
    <tr class="il wd4">
        <td class="il wd4"><span class="il wd4_statfl"
        >{word_freq_lex}</span>&nbsp;<span class="il wd4_statrl"
        >{word_rank_lex}</span>&nbsp;<span class="il wd4_statfo"
        >{word_freq_occ}</span>&nbsp;<span class="il wd4_statro"
        >{word_rank_occ}</span></td>
    </tr>
    <tr class="il sp">
        <td class="il sp {subphrase_border}"><span class="il sp_rela"
        >{subphrase_rela}</span>&nbsp;<span class="n sp_n"
        >{subphrase_number}</span></td>
    </tr>
    <tr class="il ph">
        <td class="il ph {phrase_border}"><span class="il ph_det"
        >{phrase_det}</span>&nbsp;<span class="il ph_fun"
        >{phrase_function}</span>&nbsp;<span class="il ph_typ"
        >{phrase_typ}</span>&nbsp;<span class="il ph_rela"
        >{phrase_rela}</span>&nbsp;<span class="a il ph_arela"
        >{phrase_atom_rela}</span>&nbsp;<span class="n a ph_an"
        >{phrase_atom_number}</span>&nbsp;<span class="n ph_n"
        >{phrase_number}</span></td>
    </tr>
    <tr class="il cl">
        <td class="il cl {clause_border}"><span class="il cl_txt"
        >{clause_txt}</span>&nbsp;<span class="il cl_typ"
        >{clause_typ}</span>&nbsp;<span class="il cl_rela"
        >{clause_rela}</span>&nbsp;<span class="a cl_tab"
        >{clause_atom_tab}</span>&nbsp;<span class="a cl_par"
        >{clause_atom_pargr}</span>&nbsp;<span class="a cl_code"
        >{clause_atom_code}</span>&nbsp;<span class="n a cl_an"
        >{clause_atom_number}</span>&nbsp;<span class="n cl_n"
        >{clause_number}</span></td>
    </tr>
    <tr class="il sn">
        <td class="il sn {sentence_border}"><span class="n a sn_an"
        >{sentence_atom_number}</span>&nbsp;<span class="n sn_n"
        >{sentence_number}</span></td>
    </tr>
</table>"""


CACHING = True
CACHING_RAM_ONLY = True


def from_cache(cache, ckey, func, expire):
    if CACHING:
        if CACHING_RAM_ONLY:
            result = cache.ram(ckey, func, time_expire=expire)
        else:
            result = cache.ram(
                ckey,
                lambda: cache.disk(ckey, func, time_expire=expire),
                time_expire=expire,
            )
    else:
        result = func()
    return result


def clear_cache(cache, ckeys):
    cache.ram.clear(regex=ckeys)
    if not CACHING_RAM_ONLY:
        cache.disk.clear(regex=ckeys)


def get_books(passage_dbs, vr):  # get book information: number of chapters per book
    if vr in passage_dbs:
        books_data = passage_dbs[vr].executesql(
            """
select book.id, book.name, max(chapter_num)
from chapter inner join book
on chapter.book_id = book.id group by name order by book.id
;
"""
        )
        books_order = [x[1] for x in books_data]
        books = dict((x[1], x[2]) for x in books_data)
        book_id = dict((x[1], x[0]) for x in books_data)
        book_name = dict((x[0], x[1]) for x in books_data)
        result = (books, books_order, book_id, book_name)
    else:
        result = ({}, [], {}, {})
    return result


def iid_encode(qw, idpart, kw=None, sep="|"):
    if qw == "n":
        return (
            b64encode(("{}|{}".format(idpart, kw)).encode("utf8"))
            .decode("utf8")
            .replace("\n", "")
            .replace("=", "_")
        )
    if qw == "w":
        return idpart
    if qw == "q":
        return str(idpart)
    return str(idpart)


def iid_decode(qw, iidrep, sep="|", rsep=None):
    idpart = iidrep
    kw = ""
    if qw == "n":
        try:
            (idpart, kw) = (
                b64decode(iidrep.replace("_", "=").encode("utf8"))
                .decode("utf8")
                .split(sep, 1)
            )
        except Exception:
            (idpart, kw) = (None, None)
    if qw == "w":
        (idpart, kw) = (iidrep, "")
    if qw == "q":
        (idpart, kw) = (int(iidrep) if iidrep.isdigit() else 0, "")
    if rsep is None:
        result = (idpart, kw)
    else:
        if qw == "n":
            result = rsep.join((str(idpart), kw))
        else:
            result = str(idpart)
    return result


def vcompile(tp):
    if tp == "bool":
        return lambda d, x: x if x in {"x", "v"} else d
    (t, v) = tp.split(":")
    if t == "alnum":
        return (
            lambda d, x: x
            if x is not None
            and len(str(x)) < int(v)
            and str(x).replace("_", "").replace(" ", "").isalnum()
            else d
        )
    elif t == "base64":
        return (
            lambda d, x: d
            if x is None
            else x
            if (type(x) is str or type(x) is str)
            and len(x) < int(v)
            and x.replace("_", "").isalnum()
            else d
        )
    elif t == "int":
        (lowest, highest) = v.split("-")
        return (
            lambda d, x: int(x)
            if x is not None
            and str(x).isdigit()
            and int(x) >= int(lowest)
            and int(x) <= int(highest)
            else int(d)
            if d is not None
            else d
        )
    elif t == "enum":
        vals = set(vcolors.keys()) if v == "color" else set(v.split(","))
        return lambda d, x: x if x is not None and x in vals else d


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
            this_initk = initk[i]
            if this_initk == "None":
                this_initk = ""
            settings[group][qw][f] = this_initk
            validation[group][qw][f] = valtype[i]


def get_request_val(group, qw, f, default=True):
    rvar = ("c_" if group == "colormap" else "") + qw + f
    if rvar == "iid":
        x = current.request.vars.get("id", current.request.vars.get("iid", None))
    else:
        x = current.request.vars.get(rvar, None)
        if rvar == "extra":
            x = str(x)
    if type(x) is list:
        x = x[0]
        # this occurs when the same variable occurs multiple times
        # in the request/querystring
    fref = "0" if group == "colormap" else f
    d = settings[group][qw][fref] if default else None
    return validation[group][qw][fref](d, x)


def make_ccolors():
    ccolor_proto = [tuple(cc.split(",")) for cc in ccolor_spec.strip().split()]
    ccolors = []
    prevl = 0
    for (l, z) in ccolor_proto:
        newl = int(l) + 1
        for i in range(prevl, newl):
            ccolors.append(z)
        prevl = newl
    return ccolors


if nrows * ncols != len(vcolornames):
    print(
        "View settings: mismatch in number of colors: {} * {} != {}".format(
            nrows, ncols, len(vcolornames)
        )
    )
if dnrows * dncols != len(vdefaultcolors):
    print(
        "View settings: mismatch in number of default colors: {} * {} != {}".format(
            dnrows, dncols, len(vdefaultcolors)
        )
    )


def ccell(qw, iid, c):
    return '\t\t<td class="c{qw} {qw}{iid}"><a href="#">{n}</a></td>'.format(
        qw=qw, iid=iid, n=vcolornames[c]
    )


def crow(qw, iid, r):
    return "\t<tr>\n{}\n\t</tr>".format(
        "\n".join(ccell(qw, iid, c) for c in range(r * ncols, (r + 1) * ncols))
    )


def ctable(qw, iid):
    return '<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'.format(
        qw=qw, iid=iid, cs="\n".join(crow(qw, iid, r) for r in range(nrows))
    )


def vsel(qw, iid, typ):
    content = "&nbsp;" if qw == "q" else "w"
    selc = (
        ""
        if typ
        else """<span class="pickedc cc_selc_{qw}"
        ><input type="checkbox" id="selc_{qw}{iid}" name="selc_{qw}{iid}"
        /></span>&nbsp;"""
    )
    sel = """<span class="picked cc_sel_{qw}" id="sel_{qw}{iid}"
    ><a href="#">{lab}</a></span>"""
    return (selc + sel).format(qw=qw, iid=iid, lab=content)


def colorpicker(qw, iid, typ):
    return "{s}{p}\n".format(s=vsel(qw, iid, typ), p=ctable(qw, iid))


def get_fields(tp, qw=qw):
    if qw is None or qw != "n":
        if tp == "txt_il":
            thesehfields = []
            for (line, fields) in hebrewdata_lines:
                if get_request_val("hebrewdata", "", line) == "v":
                    for (f, name, pretty_name) in fields:
                        if get_request_val("hebrewdata", "", f) == "v":
                            thesehfields.append((name, pretty_name))
        else:
            thesehfields = hfields[tp]
        return thesehfields
    else:
        if tp == "txt_p":
            fields = (
                ("clause_atom", "ca_nr"),
                ("shebanq_note.note.keywords", "keyw"),
                ("shebanq_note.note.status", "status"),
                ("shebanq_note.note.ntext", "note"),
            )
        else:
            fields = (
                ("clause_atom", "ca_nr"),
                ("clause_atom.text", "ca_txt"),
                ("shebanq_note.note.keywords", "keyw"),
                ("shebanq_note.note.status", "status"),
                ("shebanq_note.note.ntext", "note"),
                ("shebanq_note.note.created_on", "created_on"),
                ("shebanq_note.note.modified_on", "modified_on"),
                ('if(shebanq_note.note.is_shared = "T", "T", "F") as shared', "shared"),
                (
                    'if(shebanq_note.note.is_published = "T", "T", "F") as published',
                    "published",
                ),
                ('ifnull(shebanq_note.note.published_on, "") as pub', "published_on"),
            )
        return fields


class Viewsettings:
    def __init__(self, cache, passage_dbs, URL, versions):
        self.cache = cache
        self.passage_dbs = passage_dbs
        self.URL = URL

        self.state = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )
        self.pref = get_request_val("rest", "", "pref")

        self.versions = {
            v: info for (v, info) in versions.items() if info["present"] is not None
        }

        for group in settings:
            self.state[group] = {}
            for qw in settings[group]:
                self.state[group][qw] = {}
                from_cookie = {}
                # if current.request.cookies.has_key(self.pref + group + qw):
                if (self.pref + group + qw) in current.request.cookies:
                    if self.pref == "my":
                        try:
                            from_cookie = json.loads(
                                urllib.parse.unquote(
                                    current.request.cookies[
                                        self.pref + group + qw
                                    ].value
                                )
                            )
                        except ValueError:
                            pass
                if group == "colormap":
                    for fid in from_cookie:
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            vstate = validation[group][qw]["0"](None, from_cookie[fid])
                            if vstate is not None:
                                self.state[group][qw][fid] = vstate
                    for f in current.request.vars:
                        if not f.startswith("c_{}".format(qw)):
                            continue
                        fid = f[3:]
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            vstate = get_request_val(group, qw, fid, default=False)
                            if vstate is not None:
                                from_cookie[fid] = vstate
                                self.state[group][qw][fid] = vstate
                elif group != "rest":
                    for f in settings[group][qw]:
                        init = settings[group][qw][f]
                        vstate = validation[group][qw][f](
                            init, from_cookie.get(f, None)
                        )
                        vstater = get_request_val(group, qw, f, default=False)
                        if vstater is not None:
                            vstate = vstater
                        from_cookie[f] = vstate
                        self.state[group][qw][f] = vstate

                if group != "rest":
                    current.response.cookies[
                        self.pref + group + qw
                    ] = urllib.parse.quote(json.dumps(from_cookie))
                    current.response.cookies[self.pref + group + qw]["expires"] = (
                        30 * 24 * 3600
                    )
                    current.response.cookies[self.pref + group + qw]["path"] = "/"

        books = {}
        books_order = {}
        book_id = {}
        book_name = {}

        self.books = books
        self.books_order = books_order
        self.book_id = book_id
        self.book_name = book_name

        cache = self.cache
        passage_dbs = self.passage_dbs

        for (v, vinfo) in self.versions.items():
            if not vinfo["present"]:
                continue
            (books[v], books_order[v], book_id[v], book_name[v]) = from_cache(
                cache, "books_{}_".format(v), lambda: get_books(passage_dbs, v), None
            )

    def theversion(self):
        return self.state["material"][""]["version"]

    def versionstate(self):
        return self.state["material"][""]["version"]

    def writeConfig(self):
        URL = self.URL

        return """
var Config = {{
versions: {versions},
vcolors: {vcolors},
ccolors: {ccolors},
vdefaultcolors: {vdefaultcolors},
dncols: {dncols},
dnrows: {dnrows},
viewinit: {initstate},
style: {style},
pref: {pref},
tp_labels: {tp_labels},
tr_labels: {tr_labels},
tab_info: {tab_info},
tab_views: {tab_views},
tr_info: {tr_info},
next_tp: {next_tp},
next_tr: {next_tr},
nt_statclass: {nt_statclass},
nt_statsym: {nt_statsym},
nt_statnext: {nt_statnext},
bookla: {bookla},
booktrans: {booktrans},
booklangs: {booklangs},
books: {books},
booksorder: {booksorder},
featurehost: "{featurehost}",
bol_url: "{bol_url}",
pbl_url: "{pbl_url}",
host: "{host}",
query_url: "{query_url}",
word_url: "{word_url}",
words_url: "{words_url}",
note_url: "{note_url}",
notes_url: "{notes_url}",
field_url: "{field_url}",
fields_url: "{fields_url}",
cnotes_url: "{cnotes_url}",
page_view_url: "{page_view_url}",
view_url: "{view_url}",
material_url: "{material_url}",
data_url: "{data_url}",
side_url: "{side_url}",
item_url: "{item_url}",
chart_url: "{chart_url}",
pn_url: "{pn_url}",
n_url: "{n_url}",
upload_url: "{upload_url}",
pq_url: "{pq_url}",
queriesr_url: "{queriesr_url}",
q_url: "{q_url}",
record_url: "{record_url}",
}}
""".format(
            vdefaultcolors=json.dumps(vdefaultcolors),
            initstate=json.dumps(self.state),
            vcolors=json.dumps(vcolors),
            ccolors=json.dumps(make_ccolors()),
            style=json.dumps(style),
            pref='"{}"'.format(self.pref),
            dncols=dncols,
            dnrows=dnrows,
            versions=json.dumps(
                [v for (v, inf) in self.versions.items() if inf["present"]]
            ),
            tp_labels=json.dumps(tp_labels),
            tr_labels=json.dumps(tr_labels),
            tab_info=json.dumps(tab_info),
            tab_views=tab_views,
            tr_info=json.dumps(tr_info),
            next_tp=json.dumps(next_tp),
            next_tr=json.dumps(next_tr),
            nt_statclass=json.dumps(nt_statclass),
            nt_statsym=json.dumps(nt_statsym),
            nt_statnext=json.dumps(nt_statnext),
            bookla=json.dumps(booknames[biblang]["la"]),
            booktrans=json.dumps(booktrans),
            booklangs=json.dumps(booklangs[biblang]),
            booksorder=json.dumps(self.books_order),
            books=json.dumps(self.books),
            featurehost="https://etcbc.github.io/bhsa/features",
            bol_url="http://bibleol.3bmoodle.dk/text/show_text",
            pbl_url="https://parabible.com",
            host=URL("hebrew", "text", host=True),
            query_url=URL("hebrew", "query", "", host=True),
            word_url=URL("hebrew", "word", "", host=True),
            words_url=URL("hebrew", "words", extension=""),
            note_url=URL("hebrew", "note", "", host=True),
            notes_url=URL("hebrew", "notes", "", host=True),
            field_url=URL("hebrew", "field", extension="json"),
            fields_url=URL("hebrew", "fields", extension="json"),
            cnotes_url=URL("hebrew", "cnotes", extension="json"),
            page_view_url=URL("hebrew", "text", host=True),
            view_url=URL("hebrew", "text", host=True),
            material_url=URL("hebrew", "material", host=True),
            data_url=URL("hebrew", "verse", host=True),
            side_url=URL("hebrew", "side", host=True),
            item_url=URL("hebrew", "item.csv", host=True),
            chart_url=URL("hebrew", "chart", host=True),
            pn_url=URL("hebrew", "note_tree", extension="json"),
            n_url=URL("hebrew", "text", extension=""),
            upload_url=URL("hebrew", "note_upload", extension="json"),
            pq_url=URL("hebrew", "query_tree", extension="json"),
            queriesr_url=URL("hebrew", "queriesr", extension="json"),
            q_url=URL("hebrew", "text", extension=""),
            record_url=URL("hebrew", "record", extension="json"),
        )


def h_esc(material, fill=True):
    material = (
        material.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
        .replace("\\n", "\n")
    )
    if fill:
        if material == "":
            material = "&nbsp;"
    return material


def verse_simple(passage_dbs, vr, bk, ch, vs):
    passage_db = passage_dbs[vr] if vr in passage_dbs else None
    msgs = []
    good = True
    data = dict()
    if passage_db is None:
        msgs.append(("Error", "No such version: {}".format(vr)))
        good = False
    if good:
        verse_info = passage_db.executesql(
            """
select verse.id, verse.text from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
where book.name = '{}' and chapter.chapter_num = {} and verse_num = {}
;
""".format(
                bk, ch, vs
            )
        )
        if len(verse_info) == 0:
            msgs.append(("Error", "No such verse: {} {}:{}".format(bk, ch, vs)))
            good = False
        else:
            data = verse_info[0]
            vid = data[0]
            word_info = passage_db.executesql(
                """
select word.word_phono, word.word_phono_sep
from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
where verse.id = {}
order by word_number
;
""".format(
                    vid
                )
            )
            data = dict(text=data[1], phonetic="".join(x[0] + x[1] for x in word_info))
    return json.dumps(dict(good=good, msgs=msgs, data=data), ensure_ascii=False)


class Verses:
    def __init__(
        self,
        passage_dbs,
        vr,
        mr,
        verse_ids=None,
        chapter=None,
        tp=None,
        tr=None,
        lang="en",
    ):
        if tr is None:
            tr = "hb"
        self.version = vr
        passage_db = passage_dbs[vr] if vr in passage_dbs else None
        self.mr = mr
        self.tp = tp
        self.tr = tr
        self.verses = []
        if self.mr == "r" and (verse_ids is None or len(verse_ids) == 0):
            return
        verse_ids_str = (
            ",".join((str(v) for v in verse_ids)) if verse_ids is not None else None
        )
        cfield = "verse.id"
        cwfield = "word_verse.verse_id"
        condition_pre = (
            """
where {{}} in ({})
""".format(
                verse_ids_str
            )
            if verse_ids is not None
            else """
where chapter_id = {}
""".format(
                chapter
            )
            if chapter is not None
            else ""
        )
        condition = condition_pre.format(cfield)
        wcondition = condition_pre.format(cwfield)

        verse_info = (
            passage_db.executesql(
                """
select verse.id, book.name, chapter.chapter_num, verse.verse_num{} from verse
inner join chapter on verse.chapter_id=chapter.id
inner join book on chapter.book_id=book.id
{}
order by verse.id
;
""".format(
                    ", verse.xml" if tp == "txt_p" else "", condition
                )
            )
            if passage_db
            else []
        )

        word_records = []
        word_records = (
            passage_db.executesql(
                """
select {}, verse_id, lexicon_id from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
{}
order by word_number
;
""".format(
                    ",".join(field_names[tp]), wcondition
                ),
                as_dict=True,
            )
            if passage_db
            else []
        )

        word_data = collections.defaultdict(lambda: [])
        for record in word_records:
            word_data[record["verse_id"]].append(
                dict(
                    (
                        x,
                        h_esc(
                            str(y), not (x.endswith("_border") or x in notfillfields)
                        ),
                    )
                    for (x, y) in record.items()
                )
            )

        for v in verse_info:
            v_id = int(v[0])
            xml = v[4] if tp == "txt_p" else ""
            self.verses.append(
                Verse(
                    passage_dbs,
                    vr,
                    v[1],
                    v[2],
                    v[3],
                    xml=xml,
                    word_data=word_data[v_id],
                    tp=tp,
                    tr=tr,
                    mr=mr,
                    lang=lang,
                )
            )


class Verse:
    def __init__(
        self,
        passage_dbs,
        vr,
        book_name,
        chapter_num,
        verse_num,
        xml=None,
        word_data=None,
        tp=None,
        tr=None,
        mr=None,
        lang="en",
    ):
        self.version = vr
        passage_db = passage_dbs[vr] if vr in passage_dbs else None
        self.tp = tp
        self.tr = tr
        self.mr = mr
        self.lang = lang
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        if xml is None:
            xml = ""
        if word_data is None:
            wsql = """
select {}, lexicon_id from word
inner join word_verse on word_number = word_verse.anchor
inner join verse on verse.id = word_verse.verse_id
inner join chapter on verse.chapter_id = chapter.id
inner join book on chapter.book_id = book.id
where book.name = '{}' and chapter.chapter_num = {} and verse.verse_num = {}
order by word_number
;
""".format(
                ",".join(field_names["txt_il"]), book_name, chapter_num, verse_num
            )
            word_records = (
                passage_db.executesql(wsql, as_dict=True) if passage_db else []
            )
            word_data = []
            for record in word_records:
                word_data.append(
                    dict(
                        (
                            (
                                x,
                                h_esc(
                                    str(y),
                                    not (x.endswith("_border") or x in notfillfields),
                                ),
                            )
                            for (x, y) in record.items()
                        ),
                    )
                )
        self.xml = xml
        self.word_data = word_data
        self.words = []

    # def chapter_link(self): return (self.book_name, self.chapter_num)
    # def verse_link(self): return (self.book_name, self.chapter_num, self.verse_num)

    def label(self):
        return (
            booktrans[self.lang][self.book_name].replace("_", " "),
            self.book_name,
            self.chapter_num,
            self.verse_num,
        )

    def get_words(self):
        if len(self.words) == 0:
            root = ET.fromstring("<verse>{}</verse>".format(self.xml).encode("utf-8"))
            i = 0
            for child in root:
                monad_id = int(child.attrib["m"])
                lex_id = child.attrib["l"]
                text = "" if child.text is None else child.text
                wdata = self.word_data[i]
                phtext = wdata["word_phono"]
                phsep = wdata["word_phono_sep"]
                trailer = child.get("t", "")
                self.words.append((monad_id, lex_id, text, trailer, phtext, phsep))
                i += 1
        return self.words

    def material(self, user_agent):
        if self.tp == "txt_p":
            return self._plain_text(user_agent)
        elif self.tp == "txt_tb1":
            return self._tab1_text(user_agent)
        elif self.tp == "txt_tb2":
            return self._tab2_text(user_agent)
        elif self.tp == "txt_tb3":
            return self._tab3_text(user_agent)
        elif self.tp == "txt_il":
            return self._rich_text(user_agent)

    def _plain_text(self, user_agent):
        material = []
        for word in self.get_words():
            if self.tr == "hb":
                # no longer needed because the browser now render Hebrew text properly
                # atext = adapted_text(word[2], user_agent)
                atext = word[2]
                sep = word[3]
            elif self.tr == "ph":
                atext = word[4]
                sep = word[5]
            material.append(
                """<span m="{}" l="{}">{}</span>{}""".format(
                    word[0], word[1], atext, sep
                )
            )
        return "".join(material)

    def _rich_text(self, user_agent):
        material = []
        for word in self.word_data:
            material.append(text_tpl.format(**word))
        return "".join(material)

    def _tab1_text(self, user_agent):
        material = ["""<table class="t1_table">"""]
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca1(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca1(curca))
        material.append("</table>")
        return "".join(material)

    def _tab2_text(self, user_agent):
        material = ['<dl class="lv2">']
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca2(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca2(curca))
        material.append("</dl>")
        return "".join(material)

    def _tab3_text(self, user_agent):
        material = ['<dl class="lv3">']
        curnum = (0, 0, 0)
        curca = []
        for word in self.word_data:
            thisnum = (
                word["sentence_number"],
                word["clause_number"],
                word["clause_atom_number"],
            )
            if thisnum != curnum:
                material.append(self._putca3(curca))
                curca = []
                curnum = thisnum
            curca.append(word)
        material.append(self._putca3(curca))
        material.append("</dl>")
        return "".join(material)

    def _putca1(self, words):
        if len(words) == 0:
            return ""
        txttp = words[0]["clause_txt"].replace("?", "")
        ctp = words[0]["clause_typ"]
        tabn = int(words[0]["clause_atom_tab"])
        canr = int(words[0]["clause_atom_number"])
        # tab = '<span class="fa fa-plus-square">&#xf0fe;</span>' * tabn # plus square
        # tab = '&gt;' * tabn # plus square
        tab10s = int(tabn // 10)
        tab10r = tabn % 10
        smalltab = "&lt;" * tab10r
        bigtab = "&lt;" * tab10s
        result = [
            """
<tr canr="{canr}">
    <td colspan="3" class="t1_txt">
""".format(
                canr=canr,
            )
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(
                    """<span class="t1_phf1"
                    >{}</span><span class="t1_phfn">{}</span>""".format(
                        word["phrase_function"],
                        word["phrase_number"],
                    )
                )
            if self.tr == "hb":
                wtext = word["word_heb"]
            elif self.tr == "ph":
                wtext = word["word_phono"] + word["word_phono_sep"]
            result.append(
                """<span m="{}" l="{}">{}</span>""".format(
                    word["word_number"], word["lexicon_id"], wtext
                )
            )
        result.append(
            """
    </td>
    <td class="t1_tb1">{smalltab}</td>
    <td class="t1_tb10">{bigtab}</td>
    <td class="t1_txttp">{txttp}</td>
    <td class="t1_ctp">{ctp}</td>
</tr>
""".format(
                smalltab=smalltab,
                bigtab=bigtab,
                txttp=txttp,
                ctp=ctp,
            )
        )
        return "".join(result)

    def _putca2(self, words):
        if len(words) == 0:
            return ""
        txt = words[0]["clause_txt"]
        ctp = words[0]["clause_typ"]
        code = words[0]["clause_atom_code"]
        tabn = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabn  # arrow-left
        result = [
            """<dt class="lv2"><span class="ctxt2"
            >{}</span> <span class="ctp2">{}</span> <span class="ccode2"
            >{}</span></dt><dd class="lv2"
            ><span class="tb2">{}</span>&nbsp;""".format(
                txt,
                ctp,
                code,
                tab,
            )
        ]
        for word in words:
            if "r" in word["phrase_border"]:
                result.append(
                    ' <span class="phf2">{}</span> '.format(word["phrase_function"])
                )
            if self.tr == "hb":
                wtext = word["word_heb"]
            elif self.tr == "ph":
                wtext = word["word_phono"] + word["word_phono_sep"]
            result.append(
                '<span m="{}" l="{}">{}</span> '.format(
                    word["word_number"], word["lexicon_id"], wtext
                )
            )
        result.append("</dd>")
        return "".join(result)

    def _putca3(self, words):
        if len(words) == 0:
            return ""
        tabn = int(words[0]["clause_atom_tab"])
        tab = '<span class="fa">&#xf060;</span>' * tabn  # arrow-left
        result = [
            '<dt class="lv3"><span class="tb3">{}</span></dt><dd class="lv3">'.format(
                tab,
            )
        ]
        phrb_table = dict(
            rr="&nbsp;",  # arrow-circle-right
            r='<span class="fa">&#xf105;</span>',  # arrow-circle-o-left
            l='<span class="fa">&#xf104;</span>',  # arrow-circle-o-right
            ll="&nbsp;",  # arrow-circle-left,
        )
        for word in words:
            phrbs = word["phrase_border"].split()
            phrbsymb = ""
            phrbsyme = ""
            for phrb in phrbs:
                phrbsym = phrb_table.get(phrb, "")
                if "r" in phrb:
                    phrbsymb = phrbsym
                elif "l" in phrb:
                    phrbsyme = phrbsym
            if word["word_lex"] == "H":
                txtsym = "0d9"  # caret-left
            elif word["word_lex"] == "W":
                txtsym = "0d8"  # caret-up
            elif word["word_lex"] == "&gt;LHJM/":
                txtsym = "0ed"  #
            elif word["word_lex"] == "JHWH/":
                txtsym = "0ee"  #
            elif word["word_pos"] == "nmpr":
                if word["word_gender"] == "m":
                    txtsym = "222"  # mars
                elif word["word_gender"] == "f":
                    txtsym = "221"  # venus
                elif word["word_gender"] == "NA":
                    txtsym = "1db"  # genderless
                elif word["word_gender"] == "unknown":
                    txtsym = "1db"  # genderless
            elif word["word_pos"] == "verb":
                txtsym = "013"  # cog
            elif word["word_pos"] == "subs":
                txtsym = "146"  # minus-square
            else:
                txtsym = "068"  # minus
            result.append(
                """{}<span m="{}" l="{}"
                ><span class="fa">&#xf{};</span></span>{}""".format(
                    phrbsymb,
                    word["word_number"],
                    word["lexicon_id"],
                    txtsym,
                    phrbsyme,
                )
            )
        result.append("</dd>")
        return "".join(result)


def set_URL(URLfunction):
    global URL
    URL = URLfunction


image_pat = re.compile(
    """<a [^>]*href=['"]image[\n\t ]+([^)\n\t '"]+)['"][^>]*>(.*?)</a>"""
)


def image_repl(match):
    return """<br/><img src="{}"/><br/>{}<br/>""".format(
        match.group(1),
        match.group(2),
    )


verse_pat = re.compile(
    r"""(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+([^:)\n\t '"]+)"""
    r""":([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
)


def verse_repl(match):
    return """{}{}{}""".format(
        match.group(1),
        h_esc(
            URL(
                "hebrew",
                "text",
                host=True,
                vars=dict(
                    book=match.group(2),
                    chapter=match.group(3),
                    verse=match.group(4),
                    mr="m",
                ),
            )
        ),
        match.group(5),
    )


chapter_pat = re.compile(
    """(<a [^>]*href=['"])([^)\n\t ]+)[\n\t ]+([^)\n\t '"]+)(['"][^>]*>.*?</a>)"""
)


def chapter_repl(match):
    return """{}{}{}""".format(
        match.group(1),
        h_esc(
            URL(
                "hebrew",
                "text",
                host=True,
                vars=dict(
                    book=match.group(2), chapter=match.group(3), verse="1", mr="m"
                ),
            )
        ),
        match.group(4),
    )


shebanq_pat = re.compile("""(href=['"])shebanq:([^)\n\t '"]+['"])""")


def shebanq_repl(match):
    return """{}{}{}""".format(
        match.group(1),
        URL("hebrew", "text", host=True),
        match.group(2),
    )


feature_pat = re.compile("""(href=['"])feature:([^)\n\t '"]+)(['"])""")


def feature_repl(match):
    return """{}{}/{}{} {}""".format(
        match.group(1),
        URL("static", "docs/features", host=True),
        match.group(2),
        match.group(3),
        """ target="_blank" """,
    )


def special_links(d_md):
    d_md = image_pat.sub(image_repl, d_md)
    d_md = verse_pat.sub(verse_repl, d_md)
    d_md = chapter_pat.sub(chapter_repl, d_md)
    d_md = shebanq_pat.sub(shebanq_repl, d_md)
    d_md = feature_pat.sub(feature_repl, d_md)
    return d_md


# we need to h_esc the markdown text
# but markdown does an extra layer of escaping & inside href attributes.
# we have to unescape doubly escaped &


def sanitize(text):
    return text.replace("&amp;amp;", "&amp;")


def feed(db):
    pqueryx_sql = """
select
    query.id as qid,
    auth_user.first_name as ufname,
    auth_user.last_name as ulname,
    query.name as qname,
    query.description as qdesc,
    qe.id as qvid,
    qe.executed_on as qexe,
    qe.version as qver
from query inner join
    (
        select t1.id, t1.query_id, t1.executed_on, t1.version
        from query_exe t1
          left outer join query_exe t2
            on (
                t1.query_id = t2.query_id and
                t1.executed_on < t2.executed_on and
                t2.executed_on >= t2.modified_on
            )
        where
            (t1.executed_on is not null and t1.executed_on >= t1.modified_on) and
            t2.query_id is null
    ) as qe
on qe.query_id = query.id
inner join auth_user on query.created_by = auth_user.id
where query.is_shared = 'T'
order by qe.executed_on desc, auth_user.last_name
"""

    return db.executesql(pqueryx_sql)
