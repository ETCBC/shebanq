FIELDNAMES = dict(
    txtd="""
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
    txtp="""
        word_phono word_phono_sep
        """.strip().split(),
    txt1="""
        word_heb word_ktv word_phono word_phono_sep word_number
        phrase_border phrase_number phrase_function
        sentence_number clause_number clause_atom_number
        clause_atom_tab clause_txt clause_typ
        """.strip().split(),
    txt2="""
        word_heb word_ktv word_phono word_phono_sep word_number
        phrase_border phrase_function
        sentence_number clause_number clause_atom_number
        clause_atom_tab clause_atom_code clause_txt clause_typ
        """.strip().split(),
    txt3="""
        word_heb word_ktv word_phono word_phono_sep word_number
        word_lex word_pos word_gender
        phrase_border
        sentence_number clause_number clause_atom_number clause_atom_tab
        """.strip().split(),
)
"""Lists of field names of the data that is displayed in text presentations.

Keyed by the code of the text presentation type,
the values are combinations of data type (word, phrase, clause etc.)
and feature name (gloss, phono, gender, etc.)
"""

LEGEND = """
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
                ><span class="n l_wd1_n">slot#</span></a>
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
"""The legend as an HTML table.

See [∈ feature-legend][elem-feature-legend].
"""

TEXT_TPL = ("""<table class="il c">
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
        <td class="il tl"><span l="{lexicon_id}" class="il tl_tlv"
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
</table>""")
"""The representation of a word in data view as an HTML table.
"""
