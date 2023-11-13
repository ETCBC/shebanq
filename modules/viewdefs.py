from textwrap import dedent
import collections

from gluon import current

from constants import ALWAYS
from blang import BK_NAMES
from helpers import debug


class Make:
    """Set up the definition of all settings and parameters.

    This involves

    *   specifying value types,
    *   defining default values
    *   defining validation functions
    *   value compilation
    *   exporting settings data in Javascript to the client

    See also [{SideSettings}][sidesettings].

    Page elements:

    *   [∈ highlight-published][elem-highlight-published]
    *   [∈ highlight-reset][elem-highlight-reset]
    *   [∈ highlight-many][elem-highlight-many]
    *   [∈ highlight-custom][elem-highlight-custom]
    *   [∈ highlight-one][elem-highlight-one]
    *   [∈ highlight-off][elem-highlight-off]
    *   [∈ highlight-select-single-color][elem-highlight-select-single-color]
    """
    def __init__(self):
        nColorRows = 4
        nColorCols = 4
        nDefaultClrRows = 3
        nDefaultClrCols = 4

        colorSpec = dedent(
            """
            red,#ff0000,#ff0000,1
            salmon,#ff6688,#ee7799,1
            orange,#ffcc66,#eebb55,1
            yellow,#ffff00,#dddd00,1
            green,#00ff00,#00bb00,1
            spring,#ddff77,#77dd44,1
            tropical,#66ffcc,#55ddbb,1
            turquoise,#00ffff,#00eeee,1
            blue,#8888ff,#0000ff,1
            skye,#66ccff,#55bbff,1
            lilac,#cc88ff,#aa22ff,1
            magenta,#ff00ff,#ee00ee,1
            grey,#eeeeee,#eeeeee,0
            gray,#aaaaaa,#aaaaaa,0
            black,#000000,#000000,0
            white,#ffffff,#ffffff,0
            """
        )

        colorSpecCls = dedent(
            """
             0,z0
             1,z1
             2,z2
             5,z3
            10,z4
            20,z5
            50,z6
            51,z7
            """
        )

        colorProto = [tuple(spec.split(",")) for spec in colorSpec.strip().split()]
        colorsDefault = [x[0] for x in colorProto if x[3] == "1"]
        colorNames = [x[0] for x in colorProto]
        colors = dict((x[0], dict(q=x[1], w=x[2])) for x in colorProto)

        if nColorRows * nColorCols != len(colorNames):
            debug(
                "View settings: mismatch in number of colors: "
                f"{nColorRows} * {nColorCols} != {len(colorNames)}"
            )
        if nDefaultClrRows * nDefaultClrCols != len(colorsDefault):
            debug(
                "View settings: mismatch in number of default colors: "
                f"{nDefaultClrRows} * {nDefaultClrCols} != {len(colorsDefault)}"
            )

        tabInfo = dict(
            txt1="Notes view",
            txt2="Syntax view",
            txt3="Abstract view",
        )
        tabLabels = dict(
            txtp="text",
            txt1="Notes",
            txt2="Syntax",
            txt3="Abstract",
            txtd="data",
        )
        trInfo = ["hb", "ph"]
        trLabels = dict(
            hb="hebrew",
            ph="phonetic",
        )

        nTabViews = len(tabInfo)
        # nextTp is a mapping from a text type to the next:
        # it goes txtp => txt1 => txt2 => ... => txtp
        nextTp = dict(
            (
                "txtp" if i == 0 else f"txt{i}",
                f"txt{i + 1}" if i < nTabViews else "txtp",
            )
            for i in range(nTabViews + 1)
        )

        # nextTr is a mapping from a script type to the next: it goes hb => ph => hb
        nextTr = dict((trInfo[i], trInfo[(i + 1) % 2]) for i in range(len(trInfo)))

        noteStatusOrder = "o*+?-!"
        noteStatusCls = {
            "o": "nt_info",
            "+": "nt_good",
            "-": "nt_error",
            "?": "nt_warning",
            "!": "nt_special",
            "*": "nt_note",
        }
        noteStatusSym = {
            "o": "circle",
            "+": "check-circle",
            "-": "times-circle",
            "?": "exclamation-circle",
            "!": "info-circle",
            "*": "star",
        }
        noteStatusNxt = {}
        for (i, x) in enumerate(noteStatusOrder):
            noteStatusNxt[x] = noteStatusOrder[(i + 1) % len(noteStatusOrder)]

        featureFields = dict(
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

        featureFieldSpec = (
            dedent(
                """
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
                """
            )
            .strip()
            .split()
        )

        featureLines = []
        for item in featureFieldSpec:
            (line, fieldSpec) = item.split(":")
            fields = [x.split("=") for x in fieldSpec.split(",")]
            featureLines.append((line, tuple(fields)))

        itemStyle = dict(
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
                subtract=250,
                T="N",
                t="n",
                Tag="Note",
                tag="note",
                Tags="Notes",
                tags="notes",
            ),
            m=dict(
                subtract=250,
                T="I",
                t="i",
                Tag="Item",
                tag="item",
                Tags="Items",
                tags="items",
            ),
        )

        txtTbs = ",".join(f"txt{t}" for t in range(1, nTabViews + 1))
        trLabs = ",".join(trLabels)

        specs = dict(
            material=(
                """version book chapter verse iid page mr qw tp tr lang""",
                (
                    """alnum:10 alnum:30 int:1-150 int:1-200 base64:1024 """
                    f"""int:1-1000000 enum:m,r enum:q,w,n enum:txtp,{txtTbs},txtd """
                    f"""enum:{trLabs} enum:{BK_NAMES}"""
                ),
                {"": """2021 Genesis 1 1 None 1 m x txtp hb en"""},
            ),
            hebrewdata=(
                dedent(
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
                    """
                ),
                dedent(
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
                    """
                ),
                {
                    "": dedent(
                        """
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
                    )
                },
            ),
            highlights=(
                """get active sel_one pub""",
                """bool enum:hloff,hlone,hlcustom,hlmany enum:color bool""",
                dict(
                    q="x hlcustom grey x", w="x hlcustom gray x", n="x hlcustom black v"
                ),
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

        self.nColorRows = nColorRows
        self.nColorCols = nColorCols
        self.nDefaultClrRows = nDefaultClrRows
        self.nDefaultClrCols = nDefaultClrCols
        self.colorsDefault = colorsDefault
        self.colorSpecCls = colorSpecCls
        self.colorNames = colorNames
        self.colors = colors
        self.nTabViews = nTabViews
        self.tabInfo = tabInfo
        self.tabLabels = tabLabels
        self.trInfo = trInfo
        self.trLabels = trLabels
        self.nextTp = nextTp
        self.nextTr = nextTr
        self.noteStatusCls = noteStatusCls
        self.noteStatusSym = noteStatusSym
        self.noteStatusNxt = noteStatusNxt
        self.featureFields = featureFields
        self.featureLines = featureLines
        self.itemStyle = itemStyle
        self.specs = specs

        self.setupValidation()

    def setupValidation(self):
        specs = self.specs

        settings = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
        validation = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )

        for group in specs:
            (flds, types, init) = specs[group]
            flds = flds.strip().split()
            types = types.strip().split()
            valtype = [self.compileValues(tp) for tp in types]
            for qw in init:
                initK = init[qw].strip().split()
                for (i, f) in enumerate(flds):
                    thisInitK = initK[i]
                    if thisInitK == "None":
                        thisInitK = ""
                    settings[group][qw][f] = thisInitK
                    validation[group][qw][f] = valtype[i]

        self.settings = settings
        self.validation = validation

    def compileValues(self, tp):
        colors = self.colors

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
            vals = set(colors.keys()) if v == "color" else set(v.split(","))
            return lambda d, x: x if x is not None and x in vals else d

    def export(self):
        return {
            key: getattr(self, key)
            for key in dedent(
                """
                nColorRows
                nColorCols
                nDefaultClrRows
                nDefaultClrCols
                colorsDefault
                colorSpecCls
                colorNames
                colors
                nTabViews
                tabInfo
                tabLabels
                trInfo
                trLabels
                nextTp
                nextTr
                noteStatusCls
                noteStatusSym
                noteStatusNxt
                featureFields
                featureLines
                itemStyle
                specs
                settings
                validation
                """
            )
            .strip()
            .split()
        }


class VIEWDEFS:
    def __init__(self):
        Caching = current.Caching

        def make():
            makeObj = Make()
            return makeObj.export()

        keyValues = Caching.get("viewsettings_", make, ALWAYS)

        for (key, value) in keyValues.items():
            setattr(self, key, value)

    def colorPicker(self, qw, iid, typ):
        return f"{self.selectColor(qw, iid, typ)}{self.colorTable(qw, iid)}\n"

    def makeColors(self):
        colorSpecCls = self.colorSpecCls

        colorProtoCls = [
            tuple(spec.split(",")) for spec in colorSpecCls.strip().split()
        ]
        colorsCls = []
        lPrev = 0
        for (l, z) in colorProtoCls:
            lNew = int(l) + 1
            for i in range(lPrev, lNew):
                colorsCls.append(z)
            lPrev = lNew
        return colorsCls

    def colorTable(self, qw, iid):
        nColorRows = self.nColorRows

        cs = "\n".join(self.colorRow(qw, iid, r) for r in range(nColorRows))
        return f'<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'

    def colorRow(self, qw, iid, r):
        nColorCols = self.nColorCols

        cells = "\n".join(
            self.colorCell(qw, iid, c)
            for c in range(r * nColorCols, (r + 1) * nColorCols)
        )
        return f"\t<tr>\n{cells}\n\t</tr>"

    def colorCell(self, qw, iid, c):
        colorNames = self.colorNames

        return (
            f"""\t\t<td class="c{qw} {qw}{iid}"><a href="#">{colorNames[c]}</a></td>"""
        )

    def selectColor(self, qw, iid, typ):
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
