from gluon import current

# from helpers import debug

response.logo = A(
    IMG(_src=URL("static", "images/shebanq_logo_small.png")),
    _class="brand",
    _href=URL("default", "index"),
    _title="Home page",
    _style="margin-bottom: -2em;",
)

response.logo2 = A(
    IMG(_src=URL("static", "images/etcbc-round-small.png")),
    _class="brand",
    _href="http://www.etcbc.nl",
    _title="to the ETCBC website",
    _target="_blank",
    _style="margin-bottom: -2em;",
)

servedOn = request.env.SERVER_NAME
onLocal = False
onProd = False
onTest = False
onOther = False

if servedOn is None or servedOn.endswith("local") or servedOn.endswith("home"):
    onLocal = True
elif servedOn == "shebanq.ancient-data.org":
    onProd = True
elif servedOn == "test.shebanq.ancient-data.org":
    onTest = True
else:
    onOther = True

current.SITUATION = (
    "prod" if onProd else "test" if onTest else "local" if onLocal else "other"
)
current.DEBUG = onLocal or onTest
# debug("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")


# response.title = request.application.replace('_',' ').title()
response.title = request.function.replace("_", " ").capitalize()
response.subtitle = ""

# read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = "SHEBANQ <shebanq@ancient-data.org>"
response.meta.description = (
    "Search engine for biblical Hebrew"
    " based on the Biblia Hebraica Stuttgartensia (Amstelodamensis)"
    " database (formerly known as ETCBC, historically known as WIVU)"
)
response.meta.keywords = (
    "Hebrew, Text Database, Bible, Query, Annotation, Online Hebrew Bible, "
    "Online Bible Hebrew, Hebrew Online Bible, Hebrew Bible Reader, "
    "Hebrew Bible Search, Hebrew Bible Research, Data Science, Text Database, "
    "Linguistic Queries, WIVU, ETCBC, BHS, BHSA, Biblia Hebraica, "
    "Biblia Hebraica Stuttgartensia, Biblia Hebraica Stuttgartensia Amstelodamensis"
)
response.meta.generator = "BHSA Data"

# your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
# this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    ("" if onProd else servedOn, False, None, []),
    (T("Text"), False, URL("hebrew", "text", vars=dict(mr="m")), []),
    (T("Words"), False, URL("hebrew", "words"), []),
    (T("Queries"), False, URL("hebrew", "queries"), []),
    (T("Notes"), False, URL("hebrew", "notes"), []),
    (
        SPAN(_title="SHEBANQ Wiki", _class="fa fa-info-circle fa-2x"),
        False,
        "https://github.com/ETCBC/shebanq/wiki",
        [],
    ),
]

response.about = "https://github.com/ETCBC/shebanq/wiki"

if "auth" in locals():
    auth.wikimenu()
