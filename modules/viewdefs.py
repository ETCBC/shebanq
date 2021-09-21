import collections

from gluon import current

from blang import BK_NAMES
from helpers import debug


NROWS = 4
NCOLS = 4
DNROWS = 3
DNCOLS = 4

colorSpec = """
    red,#ff0000,#ff0000,1 salmon,#ff6688,#ee7799,1 orange,#ffcc66,#eebb55,1
    yellow,#ffff00,#dddd00,1 green,#00ff00,#00bb00,1 spring,#ddff77,#77dd44,1
    tropical,#66ffcc,#55ddbb,1 turquoise,#00ffff,#00eeee,1 blue,#8888ff,#0000ff,1
    skye,#66ccff,#55bbff,1 lilac,#cc88ff,#aa22ff,1 magenta,#ff00ff,#ee00ee,1
    grey,#eeeeee,#eeeeee,0 gray,#aaaaaa,#aaaaaa,0 black,#000000,#000000,0
    white,#ffffff,#ffffff,0
"""

colorSpecCls = """
     0,z0
     1,z1
     2,z2
     5,z3
    10,z4
    20,z5
    50,z6
    51,z7
"""

colorProto = [tuple(spec.split(",")) for spec in colorSpec.strip().split()]
COLORS_DEFAULT = [x[0] for x in colorProto if x[3] == "1"]
COLOR_NAMES = [x[0] for x in colorProto]
COLORS = dict((x[0], dict(q=x[1], w=x[2])) for x in colorProto)

if NROWS * NCOLS != len(COLOR_NAMES):
    debug(
        "View settings: mismatch in number of colors: "
        f"{NROWS} * {NCOLS} != {len(COLOR_NAMES)}"
    )
if DNROWS * DNCOLS != len(COLORS_DEFAULT):
    debug(
        "View settings: mismatch in number of default colors: "
        f"{DNROWS} * {DNCOLS} != {len(COLORS_DEFAULT)}"
    )


TAB_INFO = dict(
    txt1="Notes view",
    txt2="Syntax view",
    txt3="Abstract view",
)
TP_LABELS = dict(
    txtp="text",
    txt1="Notes",
    txt2="Syntax",
    txt3="Abstract",
    txtd="data",
)
TR_INFO = ["hb", "ph"]
TR_LABELS = dict(
    hb="hebrew",
    ph="phonetic",
)

TAB_VIEWS = len(TAB_INFO)
# NEXT_TP is a mapping from a text type to the next:
# it goes txtp => txt1 => txt2 => ... => txtp
NEXT_TP = dict(
    (
        "txtp" if i == 0 else f"txt{i}",
        f"txt{i + 1}" if i < TAB_VIEWS else "txtp",
    )
    for i in range(TAB_VIEWS + 1)
)

# NEXT_TR is a mapping from a script type to the next: it goes hb => ph => hb
NEXT_TR = dict((TR_INFO[i], TR_INFO[(i + 1) % 2]) for i in range(len(TR_INFO)))

noteStatusOrder = "o*+?-!"
NOTE_STATUS_CLS = {
    "o": "nt_info",
    "+": "nt_good",
    "-": "nt_error",
    "?": "nt_warning",
    "!": "nt_special",
    "*": "nt_note",
}
NOTE_STATUS_SYM = {
    "o": "circle",
    "+": "check-circle",
    "-": "times-circle",
    "?": "exclamation-circle",
    "!": "info-circle",
    "*": "star",
}
NOTE_STATUS_NXT = {}
for (i, x) in enumerate(noteStatusOrder):
    NOTE_STATUS_NXT[x] = noteStatusOrder[(i + 1) % len(noteStatusOrder)]

HEBREW_FIELDS = dict(
    txtp=[
        ("word_number", "slot"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_phono", "phtext"),
        ("word_phono_sep", "phsep"),
    ],
    txt1=[
        ("word_number", "slot"),
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
    txt2=[
        ("word_number", "slot"),
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
    txt3=[
        ("word_number", "slot"),
        ("word_heb", "text"),
        ("word_ktv", "ktv"),
        ("word_lex", "lexeme-t"),
        ("word_pos", "part-of-speech"),
        ("word_gender", "gender"),
        ("phrase_number", "phrase#"),
        ("clause_atom_tab", "tab"),
    ],
)

HEBREW_DATA_SPEC = """
    ht:ht_ht=word_heb=text-h,ht_hk=word_ktv=ketiv
    pt:pt=word_phono=text-p
    hl:hl_hlv=word_vlex=lexeme-v,hl_hlc=word_clex=lexeme-c
    tt:tt=word_tran=text-t
    tl:tl_tlv=word_glex=lexeme-g,tl_tlc=word_lex=lexeme-t
    gl:gl=word_gloss=gloss
    wd1:wd1_nmtp=word_nmtp=nametype,wd1_subpos=word_subpos=lexical_set,wd1_pos=word_pos=part-of-speech,wd1_pdp=word_pdp=phrase-dependent-part-of-speech,wd1_lang=word_lang=language,wd1_n=word_number=slot
    wd2:wd2_gender=word_gender=gender,wd2_gnumber=word_gnumber=number,wd2_person=word_person=person,wd2_state=word_state=state,wd2_tense=word_tense=tense,wd2_stem=word_stem=verbal_stem
    wd3:wd3_nme=word_nme=nme,wd3_pfm=word_pfm=pfm,wd3_prs=word_prs=prs,wd3_uvf=word_uvf=uvf,wd3_vbe=word_vbe=vbe,wd3_vbs=word_vbs=vbs
    wd4:wd4_statfl=word_freq_lex=freq-lex,wd4_statrl=word_rank_lex=rank-lex,wd4_statfo=word_freq_occ=freq-occ,wd4_statro=word_rank_occ=rank-occ
    sp:sp_rela=subphrase_rela=rela,sp_n=subphrase_number=subphrase#
    ph:ph_det=phrase_det=determination,ph_fun=phrase_function=function,ph_typ=phrase_typ=type-ph,ph_rela=phrase_rela=rela,ph_arela=phrase_atom_rela=rela_a,ph_an=phrase_atom_number=phrase_a#,ph_n=phrase_number=phrase#
    cl:cl_txt=clause_txt=txt,cl_typ=clause_typ=type-cl,cl_rela=clause_rela=rela,cl_tab=clause_atom_tab=tab,cl_par=clause_atom_pargr=par,cl_code=clause_atom_code=code,cl_an=clause_atom_number=clause_a#,cl_n=clause_number=clause#
    sn:sn_an=sentence_atom_number=sentence_a#,sn_n=sentence_number=sentence#
""".strip().split()
hebrewDataLines = []
for item in HEBREW_DATA_SPEC:
    (line, fieldSpec) = item.split(":")
    fields = [x.split("=") for x in fieldSpec.split(",")]
    hebrewDataLines.append((line, tuple(fields)))

SHB_STYLE = dict(
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

SETTINGS = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
VALIDATION = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))

txtTbs = ",".join(f"txt{t}" for t in range(1, TAB_VIEWS + 1))
trLabs = ",".join(TR_LABELS)

SPECS = dict(
    material=(
        """version book chapter verse iid page mr qw tp tr lang""",
        (
            """alnum:10 alnum:30 int:1-150 int:1-200 base64:1024 """
            f"""int:1-1000000 enum:m,r enum:q,w,n enum:txtp,{txtTbs},txtd """
            f"""enum:{trLabs} enum:{BK_NAMES}"""
        ),
        {"": """4 Genesis 1 1 None 1 x m txtp hb en"""},
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


def compileValues(tp):
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
        vals = set(COLORS.keys()) if v == "color" else set(v.split(","))
        return lambda d, x: x if x is not None and x in vals else d


for group in SPECS:
    (flds, types, init) = SPECS[group]
    flds = flds.strip().split()
    types = types.strip().split()
    valtype = [compileValues(tp) for tp in types]
    for qw in init:
        initK = init[qw].strip().split()
        for (i, f) in enumerate(flds):
            thisInitK = initK[i]
            if thisInitK == "None":
                thisInitK = ""
            SETTINGS[group][qw][f] = thisInitK
            VALIDATION[group][qw][f] = valtype[i]


def makeColors():
    colorProtoCls = [tuple(spec.split(",")) for spec in colorSpecCls.strip().split()]
    colorsCls = []
    lPrev = 0
    for (l, z) in colorProtoCls:
        lNew = int(l) + 1
        for i in range(lPrev, lNew):
            colorsCls.append(z)
        lPrev = lNew
    return colorsCls


def colorCell(qw, iid, c):
    return f"""\t\t<td class="c{qw} {qw}{iid}"><a href="#">{COLOR_NAMES[c]}</a></td>"""


def colorRow(qw, iid, r):
    cells = "\n".join(colorCell(qw, iid, c) for c in range(r * NCOLS, (r + 1) * NCOLS))
    return f"\t<tr>\n{cells}\n\t</tr>"


def colorTable(qw, iid):
    cs = "\n".join(colorRow(qw, iid, r) for r in range(NROWS))
    return f'<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'


def selectColor(qw, iid, typ):
    content = "&nbsp;" if qw == "q" else "w"
    selCtl = (
        ""
        if typ
        else f"""<span class="pickedc"
><input type="checkbox" id="select_{qw}{iid}" name="select_{qw}{iid}"
/></span>&nbsp;"""
    )
    sel = f"""<span class="picked colorselect_{qw}" id="sel_{qw}{iid}"
><a href="#">{content}</a></span>"""
    return selCtl + sel


def colorPicker(qw, iid, typ):
    return f"{selectColor(qw, iid, typ)}{colorTable(qw, iid)}\n"


def getFields(tp, qw=qw):
    if qw is None or qw != "n":
        if tp == "txtd":
            hebrewFields = []
            for (line, fields) in hebrewDataLines:
                if getRequestVal("hebrewdata", "", line) == "v":
                    for (f, name, prettyName) in fields:
                        if getRequestVal("hebrewdata", "", f) == "v":
                            hebrewFields.append((name, prettyName))
        else:
            hebrewFields = HEBREW_FIELDS[tp]
        return hebrewFields
    else:
        hebrewFields = (
            (
                ("clause_atom", "ca_nr"),
                ("shebanq_note.note.keywords", "keyw"),
                ("shebanq_note.note.status", "status"),
                ("shebanq_note.note.ntext", "note"),
            )
            if tp == "txtp"
            else (
                ("clause_atom", "ca_nr"),
                ("clause_atom.text", "ca_txt"),
                ("shebanq_note.note.keywords", "keyw"),
                ("shebanq_note.note.status", "status"),
                ("shebanq_note.note.ntext", "note"),
                ("shebanq_note.note.created_on", "created_on"),
                ("shebanq_note.note.modified_on", "modified_on"),
                (
                    (
                        'if(shebanq_note.note.is_shared = "T", "T", "F") '
                        'as shared'
                    ), "is_shared"),
                (
                    (
                        'if(shebanq_note.note.is_published = "T", "T", "F") '
                        'as is_published'
                    ),
                    "is_published",
                ),
                ('ifnull(shebanq_note.note.published_on, "") as pub', "published_on"),
            )
        )
        return hebrewFields


def getRequestVal(group, qw, f, default=True):
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
    d = SETTINGS[group][qw][fref] if default else None
    return VALIDATION[group][qw][fref](d, x)
