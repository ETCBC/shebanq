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
    SHB_STYLE,
    getRequestVal,
    makeColors,
)


class Viewsettings:
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
        bookId = {}
        bookName = {}

        self.books = books
        self.booksOrder = booksOrder
        self.bookId = bookId
        self.bookName = bookName

        for v in self.VERSIONS:
            (books[v], booksOrder[v], bookId[v], bookName[v]) = Chunk.getBooks(v)

    def theversion(self):
        return self.state["material"][""]["version"]

    def versionstate(self):
        return self.state["material"][""]["version"]

    def writeConfig(self):
        URL = self.URL

        return f"""
var Config = {{
versions: {json.dumps(list(self.VERSIONS))},
colorsV: {json.dumps(COLORS)},
colorsCls: {json.dumps(makeColors())},
colorsDefault: {json.dumps(COLORS_DEFAULT)},
dncols: {DNCOLS},
dnrows: {DNROWS},
viewinit: {json.dumps(self.state)},
shbStyle: {json.dumps(SHB_STYLE)},
pref: str(self.pref),
tpLabels: {json.dumps(TP_LABELS)},
trLabels: {json.dumps(TR_LABELS)},
tabInfo: {json.dumps(TAB_INFO)},
tabViews: {TAB_VIEWS},
trInfo: {json.dumps(TR_INFO)},
nextTp: {json.dumps(NEXT_TP)},
nextTr: {json.dumps(NEXT_TR)},
noteStatusCls: {json.dumps(NOTE_STATUS_CLS)},
noteStatusSym: {json.dumps(NOTE_STATUS_SYM)},
noteStatusNxt: {json.dumps(NOTE_STATUS_NXT)},
bookLatin: {json.dumps(BOOK_NAMES[BIBLANG]["la"])},
bookTrans: {json.dumps(BOOK_TRANS)},
bookLangs: {json.dumps(BOOK_LANGS[BIBLANG])},
books: {json.dumps(self.books)},
bookOrder: {json.dumps(self.booksOrder)},
featureHost: "https://etcbc.github.io/bhsa/features",
host: "{URL("hebrew", "text", host=True)}",
bolUrl: "http://bibleol.3bmoodle.dk/text/show_text",
pblUrl: "https://parabible.com",
queryUrl: "{URL("hebrew", "query", "", host=True)}",
wordUrl: "{URL("hebrew", "word", "", host=True)}",
wordsUrl: "{URL("hebrew", "words", extension="")}",
noteUrl: "{URL("hebrew", "note", "", host=True)}",
notesUrl: "{URL("hebrew", "notes", "", host=True)}",
fieldUrl: "{URL("hebrew", "field", extension="json")}",
fieldsUrl: "{URL("hebrew", "fields", extension="json")}",
verseNotesUrl: "{URL("hebrew", "versenotes", extension="json")}",
pageViewUrl: "{URL("hebrew", "text", host=True)}",
viewUrl: "{URL("hebrew", "text", host=True)}",
materialUrl: "{URL("hebrew", "material", host=True)}",
dataUrl: "{URL("hebrew", "verse", host=True)}",
sideUrl: "{URL("hebrew", "side", host=True)}",
itemUrl: "{URL("hebrew", "item.csv", host=True)}",
chartUrl: "{URL("hebrew", "chart", host=True)}",
pnUrl: "{URL("hebrew", "notetree", extension="json")}",
nUrl: "{URL("hebrew", "text", extension="")}",
uploadUrl: "{URL("hebrew", "noteupload", extension="json")}",
pqUrl: "{URL("hebrew", "querytree", extension="json")}",
queriesrUrl: "{URL("hebrew", "queriesr", extension="json")}",
qUrl: "{URL("hebrew", "text", extension="")}",
recordUrl: "{URL("hebrew", "record", extension="json")}",
}}
"""
