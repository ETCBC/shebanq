import sys

sys.path.append('/opt/emdros/lib/emdros')
import EmdrosPy
from get_db_config import config, emdros_versions

db='shebanq_etcbc'

OLD_EMDROS_VERSIONS = set(emdros_versions[0:-1])
EMDROS_VERSION = emdros_versions[-1]

def sanitize(query, msgs):
    comps = query.split('/*')
    lastcomp = comps[-1]
    if len(comps) > 1 and lastcomp.find('*/') == -1:
        result = query + '*/'
    else:
        result = query
    if 'focus' not in query.lower():
        msgs.append(('note', 'no FOCUS in your query!'))
    return result + "\nGO\n"

def to_monadsets(setstr):
    elems = setstr[2:-2].strip()
    if elems == '': return []
    comps = elems.split(',')
    return [[int(y) for y in x.lstrip().split('-')] if '-' in x else [int(x), int(x)] for x in comps]

# see the notebook mql.ipynb in the static/docs/tools/shebanq directory about
# why the following code has been developed the way it is.

#

# Now with ITER_LIMIT = 500000

ITER_LIMIT = 500000

class LimitError(Exception):
    def __init__(self, message, cause=None):
        Exception.__init__(self, message)

def sheaf_results(sheaf):
    sh_iter = sheaf.iterator()
    n = 0
    while sh_iter.hasNext():
        straw = sh_iter.current()
        n += straw_results(straw)
        if n > ITER_LIMIT: raise LimitError('')
        sh_iter.next()
    return n

def straw_results(straw):
    n = 1
    st_iter = straw.const_iterator()
    while st_iter.hasNext():
        mo = st_iter.current()
        if not mo.sheafIsEmpty():
            sheaf = mo.getSheaf()
            n *= sheaf_results(sheaf)
            if n > ITER_LIMIT: raise LimitError('')
        st_iter.next()
    return n

def mql(vr, query):
    env = EmdrosPy.EmdrosEnv(EmdrosPy.kOKConsole, EmdrosPy.kCSUTF8, config['shebanq_host'], config['shebanq_user'], config['shebanq_passwd'], db+vr, EmdrosPy.kMySQL)
    compiler_result = False
    msgs = []
    good = env.executeString(sanitize(query, msgs) , compiler_result, False, False)[1]
    limit_exceeded = False
    if not good:
        msgs.append(('error',  env.getCompilerError()))
        return (False, False, None, None, msgs, EMDROS_VERSION)
    else:
        if not env.isSheaf:
            msgs.append(('error', 'Result of query is not a sheaf'))
            return (False, False, None, None, msgs, EMDROS_VERSION)
        else:
            sheaf = env.getSheaf()
            if sheaf == None:
                msgs.append(('error', 'Result of query is the null sheaf'))
                return (False, False, 0, [], msgs, EMDROS_VERSION)
            else:
                try:
                    n = sheaf_results(sheaf)
                except LimitError as e:
                    n = ITER_LIMIT
                    limit_exceeded = True
                if not limit_exceeded:
                    ms = to_monadsets(sheaf.getSOM(True).toString())
                else:
                    ms = []
                    msgs.append(('error', u'''Too many results (much more than there are words in the Bible).
Try to limit results by putting a containing block around a sequence of blocks with .. between them.
Not: [word] .. [word] .. [word]
But: [chapter [word] .. [word] .. [word] ]
'''))
                return (True, limit_exceeded, n, ms, msgs, EMDROS_VERSION)
