import collections
import json
import urllib

from gluon import current

from blang import BIBLANG, booklangs, booknames, booktrans
from viewdefs import (
    SETTINGS,
    VALIDATION,
    DNCOLS,
    DNROWS,
    NEXT_TP,
    NEXT_TR,
    NT_STATCLASS,
    NT_STATSYM,
    NT_STATNEXT,
    TAB_INFO,
    TAB_VIEWS,
    TP_LABELS,
    TR_INFO,
    TR_LABELS,
    VCOLORS,
    VDEFAULTCOLORS,
    STYLE,
    getRequestVal,
    make_ccolors,
)


class Viewsettings:
    def __init__(self, Chunk, URL, versions):
        self.Chunk = Chunk
        self.URL = URL

        self.state = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )
        self.pref = getRequestVal("rest", "", "pref")

        self.versions = {v: info for (v, info) in versions.items()}

        for group in SETTINGS:
            self.state[group] = {}
            for qw in SETTINGS[group]:
                self.state[group][qw] = {}
                from_cookie = {}
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
                            vstate = VALIDATION[group][qw]["0"](None, from_cookie[fid])
                            if vstate is not None:
                                self.state[group][qw][fid] = vstate
                    for f in current.request.vars:
                        if not f.startswith(f"c_{qw}"):
                            continue
                        fid = f[3:]
                        if len(fid) <= 32 and fid.replace("_", "").isalnum():
                            vstate = getRequestVal(group, qw, fid, default=False)
                            if vstate is not None:
                                from_cookie[fid] = vstate
                                self.state[group][qw][fid] = vstate
                elif group != "rest":
                    for f in SETTINGS[group][qw]:
                        init = SETTINGS[group][qw][f]
                        vstate = VALIDATION[group][qw][f](
                            init, from_cookie.get(f, None)
                        )
                        vstater = getRequestVal(group, qw, f, default=False)
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

        for (v, vinfo) in self.versions.items():
            (books[v], books_order[v], book_id[v], book_name[v]) = Chunk.get_books(v)

    def theversion(self):
        return self.state["material"][""]["version"]

    def versionstate(self):
        return self.state["material"][""]["version"]

    def writeConfig(self):
        URL = self.URL

        return f"""
var Config = {{
versions: {json.dumps(list(self.versions))},
vcolors: {json.dumps(VCOLORS)},
ccolors: {json.dumps(make_ccolors())},
vdefaultcolors: {json.dumps(VDEFAULTCOLORS)},
dncols: {DNCOLS},
dnrows: {DNROWS},
viewinit: {json.dumps(self.state)},
style: {json.dumps(STYLE)},
pref: str(self.pref),
tp_labels: {json.dumps(TP_LABELS)},
tr_labels: {json.dumps(TR_LABELS)},
tab_info: {json.dumps(TAB_INFO)},
tab_views: {TAB_VIEWS},
tr_info: {json.dumps(TR_INFO)},
next_tp: {json.dumps(NEXT_TP)},
next_tr: {json.dumps(NEXT_TR)},
nt_statclass: {json.dumps(NT_STATCLASS)},
nt_statsym: {json.dumps(NT_STATSYM)},
nt_statnext: {json.dumps(NT_STATNEXT)},
bookla: {json.dumps(booknames[BIBLANG]["la"])},
booktrans: {json.dumps(booktrans)},
booklangs: {json.dumps(booklangs[BIBLANG])},
books: {json.dumps(self.books)},
booksorder: {json.dumps(self.books_order)},
featurehost: "https://etcbc.github.io/bhsa/features",
bol_url: "http://bibleol.3bmoodle.dk/text/show_text",
pbl_url: "https://parabible.com",
host: "{URL("hebrew", "text", host=True)}",
query_url: "{URL("hebrew", "query", "", host=True)}",
word_url: "{URL("hebrew", "word", "", host=True)}",
words_url: "{URL("hebrew", "words", extension="")}",
note_url: "{URL("hebrew", "note", "", host=True)}",
notes_url: "{URL("hebrew", "notes", "", host=True)}",
field_url: "{URL("hebrew", "field", extension="json")}",
fields_url: "{URL("hebrew", "fields", extension="json")}",
cnotes_url: "{URL("hebrew", "cnotes", extension="json")}",
page_view_url: "{URL("hebrew", "text", host=True)}",
view_url: "{URL("hebrew", "text", host=True)}",
material_url: "{URL("hebrew", "material", host=True)}",
data_url: "{URL("hebrew", "verse", host=True)}",
side_url: "{URL("hebrew", "side", host=True)}",
item_url: "{URL("hebrew", "item.csv", host=True)}",
chart_url: "{URL("hebrew", "chart", host=True)}",
pn_url: "{URL("hebrew", "note_tree", extension="json")}",
n_url: "{URL("hebrew", "text", extension="")}",
upload_url: "{URL("hebrew", "note_upload", extension="json")}",
pq_url: "{URL("hebrew", "query_tree", extension="json")}",
queriesr_url: "{URL("hebrew", "queriesr", extension="json")}",
q_url: "{URL("hebrew", "text", extension="")}",
record_url: "{URL("hebrew", "record", extension="json")}",
}}
"""
