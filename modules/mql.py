import sys
sys.path.append('/opt/emdros/lib/emdros')
import EmdrosPy
from get_db_config import config

db='shebanq_etcbc'

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

def sheaf_results(sheaf):
    sh_iter = sheaf.iterator()
    n = 0
    while sh_iter.hasNext():
        straw = sh_iter.current()
        n += straw_results(straw)
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
        st_iter.next()
    return n

def mo_results(straw):
    n = 0
    st_iter = straw.const_iterator()
    while st_iter.hasNext():
        mo = st_iter.current()
        if not mo.sheafIsEmpty():
            sheaf = mo.getSheaf()
            n += sheaf_results(sheaf)
        else:
            n += 1
        st_iter.next()
    return n

def mql(vr, query):
    env = EmdrosPy.EmdrosEnv(EmdrosPy.kOKConsole, EmdrosPy.kCSUTF8, config['shebanq_host'], config['shebanq_user'], config['shebanq_passwd'], db+vr, EmdrosPy.kMySQL)
    compiler_result = 0
    msgs = []
    good = env.executeString(sanitize(query, msgs) , compiler_result, 0, 0)[1]
    if not good:
        msgs.append(('error',  env.getCompilerError()))
        return (False, None, None, msgs)
    else:
        if not env.isSheaf:
            msgs.append(('error', 'Result of query is not a sheaf'))
            return (False, None, None, msgs)
        else:
            sheaf = env.getSheaf()
            if sheaf == None:
                msgs.append(('error', 'Result of query is the null sheaf'))
                return (False, 0, [], msgs)
            else:
                n = sheaf_results(sheaf)
                return (True, n, to_monadsets(sheaf.getSOM(True).toString()), msgs)

