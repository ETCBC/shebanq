import sys
sys.path.append('/opt/emdros/lib/emdros')
import EmdrosPy

usr='shemdros'
db='etcbc4'
pwd=''
config_path = '/opt/emdros/cfg/mql.cfg'
with open(config_path) as p:
    pwd = p.read().rstrip('\n')

def sanitize(query):
    comps = query.split('/*')
    lastcomp = comps[-1]
    if len(comps) > 1 and lastcomp.find('*/') == -1:
        result = query + '*/'
    else:
        result = query
    return result + "\nGO\n"

def to_monadsets(setstr):
    elems = setstr[2:-2].strip()
    if elems == '': return []
    comps = elems.split(',')
    return [[int(y) for y in x.lstrip().split('-')] if '-' in x else [int(x), int(x)] for x in comps]

def mql(query):
    env = EmdrosPy.EmdrosEnv(EmdrosPy.kOKConsole, EmdrosPy.kCSUTF8, "localhost", usr, pwd, db)
    compiler_result = 0
    good = env.executeString(sanitize(query) , compiler_result, 0, 0)[1]
    if not good:
        return (False, env.getCompilerError())
    else:
        if not env.isSheaf:
            return (False, 'Result of query is not a sheaf')
        else:
            sheaf = env.getSheaf()
            if sheaf == None:
                return (False, 'Result of query is the null sheaf')
            else:
                return (True, to_monadsets(env.getSheaf().getSOM(True).toString()))
