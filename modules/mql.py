import sys

sys.path.append("/opt/emdros/lib/emdros")
import EmdrosPy3 as EmdrosPy  # noqa E402
from dbconfig import CONFIG, EMDROS_VERSIONS  # noqa E402

db = "shebanq_etcbc"

OLD_EMDROS_VERSIONS = set(EMDROS_VERSIONS[0:-1])
EMDROS_VERSION = EMDROS_VERSIONS[-1]


def sanitize(query, msgs):
    comps = query.split("/*")
    lastcomp = comps[-1]
    if len(comps) > 1 and lastcomp.find("*/") == -1:
        result = query + "*/"
    else:
        result = query
    if "focus" not in query.lower():
        msgs.append(("note", "no FOCUS in your query!"))
    return result + "\nGO\n"


def toSlotSets(setstr):
    elems = setstr[2:-2].strip()
    if elems == "":
        return []
    comps = elems.split(",")
    return [
        [int(y) for y in x.lstrip().split("-")] if "-" in x else [int(x), int(x)]
        for x in comps
    ]


# see the notebook mql.ipynb in the static/docs/tools/shebanq directory about
# why the following code has been developed the way it is.

# Now with ITER_LIMIT = 500000

ITER_LIMIT = 500000


class LimitError(Exception):
    def __init__(self, message, cause=None):
        Exception.__init__(self, message)


def sheafResults(sheaf):
    itr = sheaf.iterator()
    n = 0
    while itr.hasNext():
        straw = itr.current()
        n += strawResults(straw)
        if n > ITER_LIMIT:
            raise LimitError("")
        itr.next()
    return n


def strawResults(straw):
    n = 1
    itr = straw.const_iterator()
    while itr.hasNext():
        mo = itr.current()
        if not mo.sheafIsEmpty():
            sheaf = mo.getSheaf()
            n *= sheafResults(sheaf)
            if n > ITER_LIMIT:
                raise LimitError("")
        itr.next()
    return n


def mql(vr, query):
    env = EmdrosPy.EmdrosEnv(
        EmdrosPy.kOKConsole,
        EmdrosPy.kCSUTF8,
        CONFIG["shebanqHost"],
        CONFIG["shebanqUser"],
        CONFIG["shebanqPassword"],
        db + vr,
        EmdrosPy.kMySQL,
    )
    compilerResult = False
    msgs = []
    good = env.executeString(sanitize(query, msgs), compilerResult, False, False)[1]
    limitExceeded = False
    if not good:
        msgs.append(("error", env.getCompilerError()))
        return (False, False, None, None, msgs, EMDROS_VERSION)
    else:
        if not env.isSheaf:
            msgs.append(("error", "Result of query is not a sheaf"))
            return (False, False, None, None, msgs, EMDROS_VERSION)
        else:
            sheaf = env.getSheaf()
            if sheaf is None:
                msgs.append(("error", "Result of query is the null sheaf"))
                return (False, False, 0, [], msgs, EMDROS_VERSION)
            else:
                try:
                    n = sheafResults(sheaf)
                except LimitError:
                    n = ITER_LIMIT
                    limitExceeded = True
                if not limitExceeded:
                    ms = toSlotSets(sheaf.getSOM(True).toString())
                else:
                    ms = []
                    msgs.append(
                        (
                            "error",
                            """Too many results (much more than there are words in the Bible).
Try to limit results by putting a containing block around
a sequence of blocks with .. between them.
Not: [word] .. [word] .. [word]
But: [chapter [word] .. [word] .. [word] ]
""",
                        )
                    )
                return (True, limitExceeded, n, ms, msgs, EMDROS_VERSION)
