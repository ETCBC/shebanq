from textwrap import dedent
import collections
import json
import urllib

from gluon import current

from blang import BIBLANG, BOOK_LANGS, BOOK_NAMES, BOOK_TRANS
from boiler import LEGEND


class VIEWSETTINGS:
    """Handles the settings that customize the look and feel on the page.

    In fact, all parameters that originate from the user are treated here.
    They are stored in local storage in the browser,
    to when a page is loaded, these stored settings will be merged with
    the incoming request variables, and the outcome of that will again
    be stored in `LocalStorage`.
    """

    def __init__(self, Books):
        self.Books = Books

        Check = current.Check

        self.state = collections.defaultdict(
            lambda: collections.defaultdict(lambda: {})
        )
        self.pref = Check.field("rest", "", "pref")

    def page(self):
        """Determines all settings and writes them out to Javascript.

        This is the start of rendering a page.
        At the client, the Javascript picks up the data and uses
        it to customise the view.

        Client code: [{viewstate}][viewstate]
        """

        ViewDefs = current.ViewDefs

        pageConfig = self.writeConfig()

        return dict(
            pageConfig=pageConfig,
            colorPicker=ViewDefs.colorPicker,
            legend=LEGEND,
            tabLabels=ViewDefs.tabLabels,
            trLabels=ViewDefs.trLabels,
            nTabViews=ViewDefs.nTabViews,
            trInfo=ViewDefs.trInfo,
        )

    def initState(self):
        Books = self.Books
        ViewDefs = current.ViewDefs
        Check = current.Check
        VERSIONS = current.VERSIONS

        settings = ViewDefs.settings
        validation = ViewDefs.validation

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
                                    requestCookies[self.pref + group + qw].value
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
                            validationState = Check.field(group, qw, fid, default=False)
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
                    responseCookies[self.pref + group + qw] = urllib.parse.quote(
                        json.dumps(fromCookie)
                    )
                    responseCookies[self.pref + group + qw]["expires"] = 30 * 24 * 3600
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
            (books[v], booksOrder[v], bookIds[v], bookName[v]) = Books.get(v)

    def currentVersion(self):
        """Return the current version.

        This is the version as determined by the latest request.

        See [∈ version][elem-version].
        """
        return self.state["material"][""]["version"]

    def writeConfig(self):
        ViewDefs = current.ViewDefs
        URL = current.URL
        VERSIONS = current.VERSIONS

        return dedent(
            f"""
            var Config = {{
            bookLangs: {json.dumps(BOOK_LANGS[BIBLANG])},
            bookLatin: {json.dumps(BOOK_NAMES[BIBLANG]["la"])},
            bookOrder: {json.dumps(self.booksOrder)},
            books: {json.dumps(self.books)},
            bookTrans: {json.dumps(BOOK_TRANS)},
            colorsDefault: {json.dumps(ViewDefs.colorsDefault)},
            colorsCls: {json.dumps(ViewDefs.makeColors())},
            colors: {json.dumps(ViewDefs.colors)},
            nDefaultClrCols: {ViewDefs.nDefaultClrCols},
            nDefaultClrRows: {ViewDefs.nDefaultClrRows},
            featureHost: "https://etcbc.github.io/bhsa/features",
            nextTp: {json.dumps(ViewDefs.nextTp)},
            nextTr: {json.dumps(ViewDefs.nextTr)},
            noteStatusCls: {json.dumps(ViewDefs.noteStatusCls)},
            noteStatusNxt: {json.dumps(ViewDefs.noteStatusNxt)},
            noteStatusSym: {json.dumps(ViewDefs.noteStatusSym)},
            pref: "{self.pref}",
            itemStyle: {json.dumps(ViewDefs.itemStyle)},
            nTabViews: {ViewDefs.nTabViews},
            tabInfo: {json.dumps(ViewDefs.tabInfo)},
            tabLabels: {json.dumps(ViewDefs.tabLabels)},
            trInfo: {json.dumps(ViewDefs.trInfo)},
            trLabels: {json.dumps(ViewDefs.trLabels)},
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

            getNotesVerseJsonUrl: "{URL("hebrew", "getversenotes.json")}",
            putNotesVerseJsonUrl: "{URL("hebrew", "putversenotes.json")}",
            noteUploadJsonUrl: "{URL("hebrew", "noteupload.json")}",

            itemRecordJsonUrl: "{URL("hebrew", "itemrecord.json")}",

            chartUrl: "{URL("hebrew", "chart")}",
            itemCsvUrl: "{URL("hebrew", "item.csv")}",

            bolUrl: "http://bibleol.3bmoodle.dk/text/show_text",
            pblUrl: "https://parabible.com",
            }}
            """
        )
