#!/usr/bin/env python

from get_db_config import config
from gluon.tools import Auth, Crud, Service, PluginManager
from gluon.contrib.login_methods.rpx_account import use_janrain


request.requires_https()

dc_u = config["shebanq_user"]
dc_p = config["shebanq_passwd"]
dc_h = config["shebanq_host"]

version_order = """c 2017 4b 4""".split()

CONTINUOUS = "c"

versions = {
    "4": {
        "name": "BHSA_4",
        "date": "2014-07-14",
        "desc": "First online version of the BHSA database in SHEBANQ",
        "notes": (
            "Fixed version. The data for this version is a snapshot."
            "The underlying data is in the ETCBC/BHSA Github repo."
        ),
        "present": True,
        "fixed": True,
    },
    "4b": {
        "name": "BHSA_4b",
        "date": "2015-11-03",
        "desc": "Second online version of the BHSA database",
        "notes": (
            "Fixed version. The data for this version is a snapshot."
            "The underlying data is in the ETCBC/BHSA Github repo."
        ),
        "present": True,
        "fixed": True,
    },
    "2017": {
        "name": "BHSA_2017",
        "date": "2017-10-06",
        "desc": "Third online version of the BHSA database in SHEBANQ",
        "notes": (
            "Fixed version. The data for this version is a snapshot."
            "The underlying data is in the ETCBC/BHSA Github repo."
        ),
        "present": True,
        "fixed": True,
    },
    "c": {
        "name": "BHSA_c",
        "date": "2018-08-08",
        "desc": "Current online version of the BHSA database in SHEBANQ",
        "notes": (
            "Current version. May receive occasional updates."
            "The underlying data is in the ETCBC/BHSA Github repo."
        ),
        "present": True,
        "fixed": False,
    },
}

connStr = "mysql://{}:{}@{}/{}".format(
    config["shebanq_user"],
    config["shebanq_passwd"],
    config["shebanq_host"],
    "shebanq_web",
)
# print(connStr)
db = DAL(
    connStr,
    migrate_enabled=False,  # if session table already exists
    # migrate=False, # if session table does not yet exist
)

passage_dbs = {}

note_db = DAL(
    "mysql://{}:{}@{}/{}".format(
        config["shebanq_user"],
        config["shebanq_passwd"],
        config["shebanq_host"],
        "shebanq_note",
    ),
    migrate_enabled=False,  # if session table already exists
    # migrate=False, # if session table does not yet exist
)

for vr in version_order:
    if not versions[vr]["present"]:
        continue
    passage_dbs[vr] = DAL(
        "mysql://{}:{}@{}/{}".format(dc_u, dc_p, dc_h, "shebanq_passage{}".format(vr)),
        migrate_enabled=False,
    )

# Indeed, we store sessions in the database:
session.connect(request, response, db=db)
response.generic_patterns = ["*"] if request.is_local else []

auth = Auth(db, secure=True)  # secure=True should enforce https for auth
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
