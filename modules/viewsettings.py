import collections
import json
import urllib

from gluon import current

from blang import BIBLANG, BOOK_LANGS, BOOK_NAMES, BOOK_TRANS
from viewdefs import (
    SETTINGS,
    VALIDATION,
    DNCOLS,
    DNROWS,
    NEXT_TP,
    NEXT_TR,
    NOTE_STATUS_CLS,
    NOTE_STATUS_SYM,
    NOTE_STATUS_NXT,
    TAB_INFO,
    TAB_VIEWS,
    TP_LABELS,
    TR_INFO,
    TR_LABELS,
    COLORS,
    COLORS_DEFAULT,
    ITEM_STYLE,
    getRequestVal,
    makeColors,
)


class VIEWSETTINGS:
    def __init__(self, Chunk, URL, VERSIONS):
        self.Chunk = Chunk
        self.URL = URL

        self.state = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )
        self.pref = getRequestVal("rest", "", "pref")

        self.VERSIONS = {v: info for (v, info) in VERSIONS.items()}

        for group in SETTINGS:
            self.state[group] = {}
            for qw in SETTINGS[group]:
                self.state[group][qw] = {}
                fromCookie = {}
                if (self.pref + group + qw) in current.request.cookies:
                    if self.pref == "my":
                        try:
                            fromCookie = json.loads(
                                urllib.parse.unquote(
                                    current.request.cookies[
                                        self.pref + group + qw
                                    ].value
                                )
                            )
                        except ValueError:
                            pass
                if group == "colormap":
                    for fid in fromCookie:
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            validationState = VALIDATION[group][qw]["0"](
                                None, fromCookie[fid]
                            )
                            if validationState is not None:
                                self.state[group][qw][fid] = validationState
                    for f in current.request.vars:
                        if not f.startswith(f"c_{qw}"):
                            continue
                        fid = f[3:]
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            validationState = getRequestVal(
                                group, qw, fid, default=False
                            )
                            if validationState is not None:
                                fromCookie[fid] = validationState
                                self.state[group][qw][fid] = validationState
                elif group != "rest":
                    for f in SETTINGS[group][qw]:
                        init = SETTINGS[group][qw][f]
                        validationState = VALIDATION[group][qw][f](
                            init, fromCookie.get(f, None)
                        )
                        vstater = getRequestVal(group, qw, f, default=False)
                        if vstater is not None:
                            validationState = vstater
                        fromCookie[f] = validationState
                        self.state[group][qw][f] = validationState

                if group != "rest":
                    current.response.cookies[
                        self.pref + group + qw
                    ] = urllib.parse.quote(json.dumps(fromCookie))
                    current.response.cookies[self.pref + group + qw]["expires"] = (
                        30 * 24 * 3600
                    )
                    current.response.cookies[self.pref + group + qw]["path"] = "/"

        books = {}
        booksOrder = {}
        bookIds = {}
        bookName = {}

        self.books = books
        self.booksOrder = booksOrder
        self.bookIds = bookIds
        self.bookName = bookName

        for v in self.VERSIONS:
            (books[v], booksOrder[v], bookIds[v], bookName[v]) = Chunk.getBooks(v)

    def theversion(self):
        return self.state["material"][""]["version"]

    def versionstate(self):
        return self.state["material"][""]["version"]

    def writeConfig(self):
        URL = self.URL

        return f"""
var Config = {{
bookLangs: {json.dumps(BOOK_LANGS[BIBLANG])},
bookLatin: {json.dumps(BOOK_NAMES[BIBLANG]["la"])},
bookOrder: {json.dumps(self.booksOrder)},
books: {json.dumps(self.books)},
bookTrans: {json.dumps(BOOK_TRANS)},
colorsDefault: {json.dumps(COLORS_DEFAULT)},
colorsCls: {json.dumps(makeColors())},
colorsV: {json.dumps(COLORS)},
dncols: {DNCOLS},
dnrows: {DNROWS},
featureHost: "https://etcbc.github.io/bhsa/features",
nextTp: {json.dumps(NEXT_TP)},
nextTr: {json.dumps(NEXT_TR)},
noteStatusCls: {json.dumps(NOTE_STATUS_CLS)},
noteStatusNxt: {json.dumps(NOTE_STATUS_NXT)},
noteStatusSym: {json.dumps(NOTE_STATUS_SYM)},
pref: str(self.pref),
itemStyle: {json.dumps(ITEM_STYLE)},
tabInfo: {json.dumps(TAB_INFO)},
tabViews: {TAB_VIEWS},
tpLabels: {json.dumps(TP_LABELS)},
trInfo: {json.dumps(TR_INFO)},
trLabels: {json.dumps(TR_LABELS)},
versions: {json.dumps(list(self.VERSIONS))},
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
queryTreeJsonUrl: "{URL("hebrew", "querytree.json")}",
queriesRecentJsonUrl: "{URL("hebrew", "queriesr.json")}",
notesPageUrl: "{URL("hebrew", "notes")}",
noteTreeJsonUrl: "{URL("hebrew", "notetree.json")}",

queryMetaUrl: "{URL("hebrew", "querymeta")}",
queryMetaFieldsJsonUrl: "{URL("hebrew", "querymetafields.json")}",
queryMetaFieldJsonUrl: "{URL("hebrew", "querymetafield.json")}",
notesVerseJsonUrl: "{URL("hebrew", "versenotes.json")}",
noteUploadJsonUrl: "{URL("hebrew", "noteupload.json")}",

chartUrl: "{URL("hebrew", "chart")}",
itemCsvUrl: "{URL("hebrew", "item.csv")}",

bolUrl: "http://bibleol.3bmoodle.dk/text/show_text",
pblUrl: "https://parabible.com",
}}
"""
