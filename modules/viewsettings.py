import collections
import json
import urllib

from gluon import current

from blang import BIBLANG, BOOK_LANGS, BOOK_NAMES, BOOK_TRANS
from boiler import LEGEND


class VIEWSETTINGS:
    def __init__(self, Pieces):
        self.Pieces = Pieces
        Check = current.Check

        self.state = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )
        self.pref = Check.field("rest", "", "pref")

    def page(self):
        ViewDefs = current.ViewDefs

        pageConfig = self.writeConfig()

        return dict(
            pageConfig=pageConfig,
            colorPicker=self.colorPicker,
            legend=LEGEND,
            tabLabels=ViewDefs["tabLabels"],
            trLabels=ViewDefs["trLabels"],
            nTabViews=ViewDefs["nTabViews"],
            trInfo=ViewDefs["trInfo"],
        )

    def initState(self):
        ViewDefs = current.ViewDefs
        Check = current.Check
        Pieces = self.Pieces
        VERSIONS = current.VERSIONS

        settings = ViewDefs["settings"]
        validation = ViewDefs["validation"]

        requestVars = current.request.vars
        requestCookies = current.request.cookies
        responseCookies = current.response.cookies

        for (group, groupSettings) in settings.items():
            self.state[group] = {}
            for qw in groupSettings:
                self.state[group][qw] = {}
                fromCookie = {}
                if (self.pref + group + qw) in requestCookies:
                    if self.pref == "my":
                        try:
                            fromCookie = json.loads(
                                urllib.parse.unquote(
                                    requestCookies[
                                        self.pref + group + qw
                                    ].value
                                )
                            )
                        except ValueError:
                            pass
                if group == "colormap":
                    for fid in fromCookie:
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            validationState = validation[group][qw]["0"](
                                None, fromCookie[fid]
                            )
                            if validationState is not None:
                                self.state[group][qw][fid] = validationState
                    for f in requestVars:
                        if not f.startswith(f"c_{qw}"):
                            continue
                        fid = f[3:]
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            validationState = Check.field(
                                group, qw, fid, default=False
                            )
                            if validationState is not None:
                                fromCookie[fid] = validationState
                                self.state[group][qw][fid] = validationState
                elif group != "rest":
                    for f in settings[group][qw]:
                        init = settings[group][qw][f]
                        validationState = validation[group][qw][f](
                            init, fromCookie.get(f, None)
                        )
                        vstater = Check.field(group, qw, f, default=False)
                        if vstater is not None:
                            validationState = vstater
                        fromCookie[f] = validationState
                        self.state[group][qw][f] = validationState

                if group != "rest":
                    responseCookies[
                        self.pref + group + qw
                    ] = urllib.parse.quote(json.dumps(fromCookie))
                    responseCookies[self.pref + group + qw]["expires"] = (
                        30 * 24 * 3600
                    )
                    responseCookies[self.pref + group + qw]["path"] = "/"

        books = {}
        booksOrder = {}
        bookIds = {}
        bookName = {}

        self.books = books
        self.booksOrder = booksOrder
        self.bookIds = bookIds
        self.bookName = bookName

        for v in VERSIONS:
            (books[v], booksOrder[v], bookIds[v], bookName[v]) = Pieces.getBooks(v)

    def theVersion(self):
        return self.state["material"][""]["version"]

    def writeConfig(self):
        ViewDefs = current.ViewDefs
        URL = current.URL
        VERSIONS = current.VERSIONS

        return f"""
var Config = {{
bookLangs: {json.dumps(BOOK_LANGS[BIBLANG])},
bookLatin: {json.dumps(BOOK_NAMES[BIBLANG]["la"])},
bookOrder: {json.dumps(self.booksOrder)},
books: {json.dumps(self.books)},
bookTrans: {json.dumps(BOOK_TRANS)},
colorsDefault: {json.dumps(ViewDefs["colorsDefault"])},
colorsCls: {json.dumps(_makeColors())},
colors: {json.dumps(ViewDefs["colors"])},
nDefaultClrCols: {ViewDefs["nDefaultClrCols"]},
nDefaultClrRows: {ViewDefs["nDefaultClrRows"]},
featureHost: "https://etcbc.github.io/bhsa/features",
nextTp: {json.dumps(ViewDefs["nextTp"])},
nextTr: {json.dumps(ViewDefs["nextTr"])},
noteStatusCls: {json.dumps(ViewDefs["noteStatusCls"])},
noteStatusNxt: {json.dumps(ViewDefs["noteStatusNxt"])},
noteStatusSym: {json.dumps(ViewDefs["noteStatusSym"])},
pref: "{self.pref}",
itemStyle: {json.dumps(ViewDefs["itemStyle"])},
nTabViews: {ViewDefs["nTabViews"]},
tabInfo: {json.dumps(ViewDefs["tabInfo"])},
tabLabels: {json.dumps(ViewDefs["tabLabels"])},
trInfo: {json.dumps(ViewDefs["trInfo"])},
trLabels: {json.dumps(ViewDefs["trLabels"])},
versions: {json.dumps(list(VERSIONS))},
viewInit: {json.dumps(self.state)},

pageShareUrl: "{URL("hebrew", "text", host=True)}",
wordShareUrl: "{URL("hebrew", "word", host=True)}",
queryShareUrl: "{URL("hebrew", "query", host=True)}",
noteShareUrl: "{URL("hebrew", "note", host=True)}",

pageUrl: "{URL("hebrew", "text")}",
pageMaterialUrl: "{URL("hebrew", "material")}",
pageSidebarUrl: "{URL("hebrew", "side")}",
verseFeaturesUrl: "{URL("hebrew", "verse")}",

wordsPageUrl: "{URL("hebrew", "words")}",
queriesPageUrl: "{URL("hebrew", "queries")}",
notesPageUrl: "{URL("hebrew", "notes")}",

queryTreeJsonUrl: "{URL("hebrew", "querytree.json")}",
noteTreeJsonUrl: "{URL("hebrew", "notetree.json")}",

queriesRecentJsonUrl: "{URL("hebrew", "queriesr.json")}",
queryUpdateJsonUrl: "{URL("hebrew", "queryupdate.json")}",
querySharingJsonUrl: "{URL("hebrew", "querysharing.json")}",

notesVerseJsonUrl: "{URL("hebrew", "versenotes.json")}",
noteUploadJsonUrl: "{URL("hebrew", "noteupload.json")}",

itemRecordJsonUrl: "{URL("hebrew", "itemrecord")}",

chartUrl: "{URL("hebrew", "chart")}",
itemCsvUrl: "{URL("hebrew", "item.csv")}",

bolUrl: "http://bibleol.3bmoodle.dk/text/show_text",
pblUrl: "https://parabible.com",
}}
"""

    def colorPicker(self, qw, iid, typ):
        return f"{_selectColor(qw, iid, typ)}{_colorTable(qw, iid)}\n"


def _selectColor(qw, iid, typ):
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


def _makeColors():
    ViewDefs = current.ViewDefs
    colorSpecCls = ViewDefs["colorSpecCls"]

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


def _colorTable(qw, iid):
    ViewDefs = current.ViewDefs
    nColorRows = ViewDefs["nColorRows"]

    cs = "\n".join(_colorRow(qw, iid, r) for r in range(nColorRows))
    return f'<table class="picker" id="picker_{qw}{iid}">\n{cs}\n</table>\n'


def _colorRow(qw, iid, r):
    ViewDefs = current.ViewDefs
    nColorCols = ViewDefs["nColorCols"]

    cells = "\n".join(
        _colorCell(qw, iid, c)
        for c in range(r * nColorCols, (r + 1) * nColorCols)
    )
    return f"\t<tr>\n{cells}\n\t</tr>"


def _colorCell(qw, iid, c):
    ViewDefs = current.ViewDefs
    colorNames = ViewDefs["colorNames"]
    return (
        f"""\t\t<td class="c{qw} {qw}{iid}"><a href="#">{colorNames[c]}</a></td>"""
    )
