import os,sys, collections, glob, subprocess, time
import nbformat
from nbconvert import HTMLExporter
from nbconvert import PythonExporter

from laf.fabric import LafFabric
fabric = LafFabric()

# ABOUT
#
# This script updates SHEBANQ: code, data, docs: selectively

#===== Commands      ========================================

versions = {'4', '4b'}
#versions = {'4', '4b', '4s'}
commands = {'code', 'data', 'docs', 'all', 'none'}
flags = {'m': 'string', 'versions': 'string', 'net': 'bool', 'netonly': 'bool', 'sql': 'bool', 'sqlonly': 'bool', 'force': 'bool', 'clean': 'bool', 'dry': 'bool'}

# USAGE
#
# python UPDATE.py command command command flag=value flag=value flag=value
#
# The command specifies a set of tasks.
# The flags specify additional constraints
#
# COMMANDS
#
# code: do shebanq repo: git add commit push
#
# docs: build docs from shebanq-doc repo, do shebanq-doc repo: git add commit -m fixes push, copy built html to shebanq
#
# data: tools: generate html, generate python, run data producing notebooks, import passage dbs into local mysql, scp them to server
#
# all: do everything
#
# FLAGS (all boolean flags are False by default)
#
# dry=False|True : if True, do a dry run: show the commands executed on the command line, but do not execute them
#
# v= comma separated list of versions: if absent, do all versions, otherwise only do indicated versions
#
# net=False|True : if False, skip all network operations
#
# netonly=False|True : if True, do only network operations
#
# sql=False|True : if False, skip mysql import steps
#
# sqlonly=False | True : if False, do only sql operations
#
# force=False|True : if False, do all actions, even if checks say that results are already up to date
#
# clean=False|True : if True, do a clean build of the feature documentation
#
# m=text : commit message for shebanq repo (default: 'fixes') (shebanq-doc repo always gets 'fixes' as commit text)

#===== Directories with notebooks that must be refreshed ====

refresh_paths = dict(
    html='''
tools/parallel
tools/phono
tools/shebanq
tools/trees
tools/valence
tools/verbsystem
tools/verbsystem/files
''',
    python='''
tools/phono/phono.ipynb
tools/shebanq/lexicon.ipynb
tools/shebanq/laf2shebanq.ipynb
''',
)

#===== Repo doc paths ======================================

shebanq_repo = os.path.abspath('../..')
featuredoc_repo = os.path.abspath('../../../shebanq-doc')
featuredoc_docs = '{}/docs'.format(featuredoc_repo)
featuredoc_src = '{}/_build/html'.format(featuredoc_docs)
featuredoc_dst = 'featuredoc'

#===== Server settings ========================================

server_user = 'dirkr'
server = 'shebanq.ancient-data.org'
server_path = '/home/dirkr/shebanq-install'

#===== End Config ============================================

html_exporter = HTMLExporter({"Exporter":{"template_file":"full"}})
python_exporter = PythonExporter()

def tweaklinks(body): return body.replace('.ipynb', '.html')

nb_conv_fmt = dict(
    html=('.html', html_exporter, tweaklinks),
    python=('.py', python_exporter, None),
) 

orig_dir = os.getcwd()

def reset_time():
    global timestamp
    timestamp = time.time()

def elapsed():
    interval = time.time() - timestamp
    if interval < 10: return "{: 2.2f}s".format(interval)
    interval = int(round(interval))
    if interval < 60: return "{:>2d}s".format(interval)
    if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
    return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

def msg(msg, newline=True, withtime=True):
    timed_msg = "{:>7} ".format(elapsed()) if withtime else ''
    timed_msg += msg
    if newline: timed_msg += "\n"
    sys.stderr.write(timed_msg)
    sys.stderr.flush()

def do_cmd(cmd, dry=False):
    good = True
    if dry:
        msg('DRY: {}'.format(cmd), withtime=False)
    else:
        good = not subprocess.call(cmd, shell=True)
    return good

def shebanq(m, net=False, netonly=False, dry=False):
    msg('begin {} ...'.format('shebanq'))
    good = False
    for x in [1]:
        if not netonly:
            msg('Updating local shebanq repo ...')
            os.chdir(shebanq_repo)
            if not do_cmd('git add --all .', dry=dry): continue
            do_cmd("git commit -m '{}'".format(m), dry=dry)
        if net: 
            msg('Pushing changes to shebanq github repo ...')
            if not do_cmd('git push origin master', dry=dry): continue
        good = True
    msg('{} {} ...'.format('ok' if good else 'failed', 'shebanq'))
    return good

def featuredoc(clean, net=False, netonly=False, dry=False):
    msg('begin {} ...'.format('featuredoc'))
    good = False
    for x in [1]:
        os.chdir(featuredoc_docs)
        if not netonly:
            msg('Building local shebanq-doc html if needed ...')
            if clean:
                if not do_cmd('make clean', dry=dry): continue
            if not do_cmd('make html', dry=dry): continue
            msg('Updating local shebanq-doc repo ...')
            os.chdir(featuredoc_repo)
            if not do_cmd('git add --all .', dry=dry): continue
            do_cmd('git commit -m fixes', dry=dry)
        if net: 
            msg('Pushing changes to shebanq-doc github repo ...')
            if not do_cmd('git push origin master', dry=dry): continue
        if not netonly:
            msg('Moving local shebanq-doc html build into place in shebanq ...')
            os.chdir(orig_dir)
            if not do_cmd('rsync -av --delete {} {}'.format(featuredoc_src.rstrip('/')+'/', featuredoc_dst), dry=dry): continue
        good = True
    msg('{} {} ...'.format('ok' if good else 'failed', 'featuredoc'))
    return good
    
def nb_convert(inpath, fmt, force=False, dry=False):
    if fmt not in nb_conv_fmt:
        msg('Format {} not recognized. Choose between {}.'.format(fmt, ', '.join(x[0] for x in nb_conv_fmt)))
        return -1

    (indir, infile) = os.path.split(inpath)
    (inbase, inext) = os.path.splitext(infile)
    if inext != '.ipynb':
        msg('Skipping {}\n'.format(inpath))
        return 0
    outpath = os.path.join(indir, inbase+nb_conv_fmt[fmt][0])
    if os.path.exists(outpath) and not force and os.path.getmtime(outpath) >= os.path.getmtime(inpath): return 0
    msg('{}{} =({})=> '.format('DRY: 'if dry else '', inpath, fmt), withtime=False, newline=False)
    if not dry:
        nb = nbformat.read(inpath, 4)
        (body, resources) = nb_conv_fmt[fmt][1].from_notebook_node(nb) 
        extra = nb_conv_fmt[fmt][2]
        if extra != None:
            body = extra(body)
        with open(outpath, 'w') as h: h.write(body)
    msg(' {}'.format(outpath), withtime=False)
    return 0 if dry else 1

def make_snapshots(fmt, force=False, dry=False):
    msg('Making {} snapshots of notebooks ...'.format(fmt))
    count = 0
    error = 0
    total = 0
    for path in refresh_paths[fmt].strip().split():
        if os.path.isdir(path):
            for nb in glob.glob('{}/*.ipynb'.format(path)):
                total += 1
                n = nb_convert(nb, fmt, force=force, dry=dry)
                if n == -1:
                    error -= n
                    continue
                count += n  
        else:
            total += 1
            n = nb_convert(path, fmt, force=force, dry=dry)
            if n == -1:
                error -= n
            else:
                count += n
    msg('{:>3} notebooks found; {:>3} already up-to-date; {:>3} converted, {:>3} errors'.format(total, total-count-error, count, error))
    return error == 0

def data_task(v, name, base, outpath, extra, force=False, dry=False, extra_inpath=None, net=False, netonly=False, sql=False, sqlonly=False):
    msg('{:<3}: begin {} ...'.format(v, name.upper()))
    os.chdir(orig_dir)
    os.chdir(base)
    inpath = '{}.py'.format(name)
    good = True
    if not netonly and not sqlonly:
        if os.path.exists(outpath) and not force and os.path.getmtime(outpath) >= os.path.getmtime(inpath) \
            and (extra_inpath == None or
                os.path.exists(outpath) and not force and os.path.getmtime(outpath) >= os.path.getmtime(extra_inpath) \
            ):
            msg('Skipped, because result is up to date: {}'.format(outpath))
        else:
            if not dry:
                with open(inpath) as f:
                    version = v
                    exec(f.read(), locals())
            else:
                msg('DRY: python {} (version={})'.format(inpath, v), withtime=False)
    if extra != None:
        this_good = extra()
        if not this_good:
            msg('ERROR in executing subsequent actions: quitting!')
            good = False
    os.chdir(orig_dir)
    msg('{:<3}: end   {} ...'.format(v, name.upper()))
    return good

def get_data_dir(source, version):
    API = fabric.load('{}{}'.format(source, version), '--', 'xxx', {"features": ('','')}, verbose='SILENT')
    return (API['data_dir'], API['my_file']('')[0:-5])

def do_all(cmds, versions=set(), net=False, netonly=False, sql=False, sqlonly=False, force=False, clean=False, m='fixes', dry=False):
    global orig_dir
    reset_time()
    orig_dir = os.getcwd()
    msg('starting in {}'.format(orig_dir))
    good = True
    for y in [1]:
        # featuredoc, tools code
        if {'docs', 'all'} & cmds:
            good = False
            for x in [1]:
                if not sqlonly: 
                    if not featuredoc(net=net, netonly=netonly, clean=clean, dry=dry): continue
                if not netonly and not sqlonly: 
                    if not make_snapshots('html', force=force, dry=dry): continue
                if not netonly and not sqlonly:
                    if not make_snapshots('python', force=force, dry=dry): continue
                good = True
            if not good: continue

        # data

        if {'data', 'all'} & cmds:
            source = 'etcbc'
            for v in sorted(versions):
                if not good: continue
                if v not in versions: continue
                good = False

                msg('Calling LAF-API for {}{}'.format(source, v))
                (data_dir, output_dir) = get_data_dir(source, v)
                phono_output = '{}/ph/phono.{}{}'.format(data_dir, source, v)
                lexicon_output = '{}/{}{}/annotations/lexicon/_header_.xml'.format(data_dir, source, v)
                passage_sql = '{}/shebanq/shebanq_passage{}.sql'.format(output_dir, v)

                def to_db():
                    os.chdir(output_dir)
                    this_good = False
                    for x in [1]:
                        if sql and not netonly:
                            msg('START importing into MYSQL: {}'.format(passage_sql))
                            if not do_cmd('mysql -u root < {}'.format(passage_sql), dry=dry): continue 
                            msg('DONE importing into MYSQL: {}'.format(passage_sql))
                        if net and not sqlonly:
                            msg('START sending to server: {}'.format(passage_sql))
                            if not do_cmd('scp -r {} {}@{}:{}'.format(passage_sql, server_user, server, server_path), dry=dry): continue
                            msg('DONE sending to server: {}'.format(passage_sql))
                        this_good = True
                    return this_good

                for x in [1]:
                    if not data_task(
                        v,
                        'phono', 'tools/phono', phono_output,
                        None,
                        force=force, dry=dry,
                        net=net, netonly=netonly, sql=sql, sqlonly=sqlonly,
                    ): continue
                    if not data_task(
                        v,
                        'lexicon', 'tools/shebanq', lexicon_output,
                        None,
                        force=force, dry=dry,
                        extra_inpath=phono_output,
                        net=net, netonly=netonly, sql=sql, sqlonly=sqlonly,
                    ): continue
                    if not data_task(
                        v,
                        'laf2shebanq', 'tools/shebanq', passage_sql,
                        to_db,
                        force=force, dry=dry,
                        extra_inpath=lexicon_output,
                        net=net, netonly=netonly, sql=sql, sqlonly=sqlonly,
                    ): continue
                    good = True

        if not good: continue

        # shebanq code
        if {'code', 'all'} & cmds: 
            good = False
            for x in [1]:
                if not sqlonly: 
                    if not shebanq(m, net=net, netonly=netonly, dry=dry): continue
                good = True
        if not good: continue

    if not good:
        msg('There were errors')
    else:
        msg('All commands completed succesfully')
    return good

bool_values = {'True': True, 'False': False}

def check_args():
    a_commands = set()
    a_flags = {}
    good = True
    for arg in sys.argv[1:]:
        fields = arg.split('=', 1)
        if len(fields) == 1:
            if arg in a_commands:
                print('Warning: repeated command: {}'.format(arg))
            else:
                a_commands.add(arg)
        else:
            (flag, val) = fields
            if flag in a_flags:
                oval = a_flags[flag]
                if oval == val:
                    print('Warning: repeated flag: {} = {}'.format(flag, val))
                else:
                    print('Warning: redefined flag: {} was {} is now {}'.format(flag, oval, val))
            a_flags[flag] =  val
    for x in a_commands:
        if x not in commands:
            print('illegal command {}: must be one of {}'.format(x, ', '.join(sorted(commands))))
            good = False
    if len(a_commands) == 0:
        print('Warning: no command specified: implied is none')
        a_commands.add('none')
    elif {'all', 'none'} & a_commands and len(a_commands) > 1:
        print('commands all and none do not go together with other commands: {}'.format(' ,'.join(sorted(a_commands))))
        good = False
    for x in a_flags:
        if x not in flags:
            print('illegal flag {}: must be one of {}'.format(x, ', '.join(sorted(flags))))
            good = False
        else:
            if flags[x] == 'bool':
                if a_flags[x] not in bool_values:
                    print('illegal value {} for flag {}: must be one of {}'.format(a_flags[x], x, ', '.join(sorted(bool_values))))
                    good = False
                else:
                    a_flags[x] = bool_values[a_flags[x]]
    for x in flags:
        if flags[x] == 'bool' and x not in a_flags: a_flags[x] = False
    if 'm' not in a_flags: a_flags['m'] = 'fixes'
    if 'versions' not in a_flags:
        a_flags['versions'] = versions
    else:
        a_versions = set(a_flags['versions'].split(','))
        for av in a_versions:
            if av not in versions:
                print('Unknown version: {}'.format(av))
                good = False
        a_flags['versions'] = a_versions
    a_net = a_flags.get('net', False)
    a_netonly = a_flags.get('netonly', False)
    if not a_net and a_netonly:
        print('Inconsistent use of flags net={} and netonly={}'.format(a_net, a_netonly))
        good = False
    a_sql = a_flags.get('sql', False)
    a_sqlonly = a_flags.get('sqlonly', False)
    if not a_sql and a_sqlonly:
        print('Inconsistent use of flags sql={} and sqlonly={}'.format(a_sql, a_sqlonly))
        good = False
    if a_sqlonly and a_netonly:
        print('Inconsistent use of flags netonly={} and sqlonly={}'.format(a_netonly, a_sqlonly))
        good = False
    return (good, a_commands, a_flags)

def work():
    (good, a_commands, a_flags) = check_args()
    good = good and do_all(a_commands, **a_flags)
    return good

work()

