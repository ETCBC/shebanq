#!/usr/bin/env python

from dbconfig import CONFIG
from gluon import current
from gluon.tools import Auth, Crud, Service, PluginManager
from gluon.contrib.login_methods.rpx_account import use_janrain


request.requires_https()

dc_u = CONFIG["shebanqUser"]
dc_p = CONFIG["shebanqPassword"]
dc_h = CONFIG["shebanqHost"]

VERSION_ORDER = """2021 c 2017 4b 4""".split()

VERSIONS = {
    "4": {
        "name": "BHSA_4",
        "date": "2014-07-14",
        "desc": "First online version of the BHSA database in SHEBANQ",
        "notes": (
            "Several unfinished features"
        ),
        "active": False,
    },
    "4b": {
        "name": "BHSA_4b",
        "date": "2015-11-03",
        "desc": "Second online version of the BHSA database",
        "notes": (
            "Fairly complete features"
        ),
        "active": False,
    },
    "2017": {
        "name": "BHSA_2017",
        "date": "2017-10-06",
        "desc": "Third online version of the BHSA database in SHEBANQ",
        "notes": (
            "Many corrections due to reanalysis of certain features"
        ),
        "active": True,
    },
    "2021": {
        "name": "BHSA_2021",
        "date": "2017-06-30",
        "desc": "Fourth online version of the BHSA database in SHEBANQ",
        "notes": (
            "More updates"
        ),
        "active": True,
    },
    "c": {
        "name": "BHSA_c",
        "date": "2018-08-08",
        "desc": "Legacy online version of the BHSA database in SHEBANQ",
        "notes": (
            "Has received occasional updates in the past, but will not change anymore."
        ),
        "active": False,
    },
}

oddVersions = ["4", "4b", "2017", "c"]
oddVersionSet = set(oddVersions)
VERSION_ORDER = oddVersions + sorted(v for v in VERSIONS if v not in oddVersionSet)
VERSION_ORDER = tuple(v for v in VERSION_ORDER)
VERSION_INDEX = dict((x[1], x[0]) for x in enumerate(VERSION_ORDER))

current.VERSIONS = VERSIONS
current.VERSION_ORDER = VERSION_ORDER
current.VERSION_INDEX = VERSION_INDEX

connUser = f"{dc_u}:{dc_p}@{dc_h}"
connStrWeb = f"mysql://{connUser}/shebanq_web"
connStrNote = f"mysql://{connUser}/shebanq_note"
connStrPassage = f"mysql://{connUser}/shebanq_passage"

db = DAL(
    connStrWeb,
    migrate_enabled=False,  # if session table already exists
    # migrate=False, # if session table does not yet exist
)
current.db = db

PASSAGE_DBS = {}
current.PASSAGE_DBS = PASSAGE_DBS

NOTE_DB = DAL(
    connStrNote,
    migrate_enabled=False,  # if session table already exists
    # migrate=False, # if session table does not yet exist
)
current.NOTE_DB = NOTE_DB

for vr in VERSION_ORDER:
    PASSAGE_DBS[vr] = DAL(
        f"{connStrPassage}{vr}",
        migrate_enabled=False,
    )

# Indeed, we store sessions in the database:
session.connect(request, response, db=db)
response.generic_patterns = ["*"] if request.is_local else []

auth = Auth(db, secure=True)  # secure=True should enforce https for auth
current.auth = auth

crud, service, plugins = Crud(db), Service(), PluginManager()
auth.define_tables(username=False, signature=False)

# configure email
mail = auth.settings.mailer
mail.settings.server = "localhost"  # 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = "shebanq@ancient-data.org"
mail.settings.login = None  # 'username:password'
mail.settings.tls = None

# configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = False
# If the user tried to access the register page but is already logged in,
# redirect to profile.
auth.settings.logged_url = URL("user", args="profile")

use_janrain(auth, filename="private/janrain.key")

auth.messages.logged_in = None
auth.messages.logged_out = None

current.URL = URL
current.LOAD = LOAD
