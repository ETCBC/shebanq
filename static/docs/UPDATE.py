import os,sys, collections, glob, subprocess, time
import nbformat
from nbconvert import HTMLExporter
from nbconvert import PythonExporter

from laf.fabric import LafFabric
fabric = LafFabric()

#===== Data versions ========================================

versions = '''
4
4b
'''

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

def shebanq(commit_msg, net=True):
    msg('begin {} ...'.format('shebanq'))
    good = False
    for x in [1]:
        msg('Updating local shebanq repo ...')
        os.chdir(shebanq_repo)
        if subprocess.call('git add --all .', shell=True): continue
        subprocess.call("git commit -m '{}'".format(commit_msg), shell=True)
        msg('Pushing changes to shebanq github repo ...')
        if net:
            if subprocess.call('git push origin master', shell=True): continue
        else:
            msg('Skipped because of net=False')
        good = True
    msg('{} {} ...'.format('ok' if good else 'failed', 'shebanq'))
    return good

def featuredoc(clean, net=True):
    msg('begin {} ...'.format('featuredoc'))
    good = False
    for x in [1]:
        os.chdir(featuredoc_docs)
        msg('Building local shebanq-doc html if needed ...')
        if clean:
            if subprocess.call('make clean', shell=True): continue
        if subprocess.call('make html', shell=True): continue
        msg('Updating local shebanq-doc repo ...')
        os.chdir(featuredoc_repo)
        if subprocess.call('git add --all .', shell=True): continue
        subprocess.call('git commit -m fixes', shell=True)
        msg('Pushing changes to shebanq-doc github repo ...')
        if net:
            if subprocess.call('git push origin master', shell=True): continue
        else:
            msg('Skipped because of net=False')
        msg('Moving local shebanq-doc html build into place in shebanq ...')
        os.chdir(orig_dir)
        if subprocess.call('rsync -av --delete {} {}'.format(featuredoc_src.rstrip('/')+'/', featuredoc_dst), shell=True): continue
        good = True
    msg('{} {} ...'.format('ok' if good else 'failed', 'featuredoc'))
    return good
    
def nb_convert(inpath, fmt, if_newer=True):
    if fmt not in nb_conv_fmt:
        msg('Format {} not recognized. Choose between {}.'.format(fmt, ', '.join(x[0] for x in nb_conv_fmt)))
        return -1

    (indir, infile) = os.path.split(inpath)
    (inbase, inext) = os.path.splitext(infile)
    if inext != '.ipynb':
        sys.stderr.write('Skipping {}\n'.format(inpath))
        return 0
    outpath = os.path.join(indir, inbase+nb_conv_fmt[fmt][0])
    if os.path.exists(outpath) and if_newer and os.path.getmtime(outpath) >= os.path.getmtime(inpath): return 0
    sys.stderr.write('{} =({})=> ... '.format(inpath, fmt))
    nb = nbformat.read(inpath, 4)
    (body, resources) = nb_conv_fmt[fmt][1].from_notebook_node(nb) 
    extra = nb_conv_fmt[fmt][2]
    if extra != None:
        body = extra(body)
    with open(outpath, 'w') as h: h.write(body)
    sys.stderr.write('=> {}\n'.format(outpath))
    return 1

def make_snapshots(fmt):
    msg('Making {} snapshots of notebooks ...'.format(fmt))
    count = 0
    error = 0
    total = 0
    for path in refresh_paths[fmt].strip().split():
        if os.path.isdir(path):
            for nb in glob.glob('{}/*.ipynb'.format(path)):
                total += 1
                n = nb_convert(nb, fmt)
                if n == -1:
                    error -= n
                    continue
                count += n  
        else:
            n = nb_convert(path, fmt)
            if n == -1:
                error -= n
            else:
                count += n
    msg('{:>3} notebooks found; {:>3} already up-to-date; {:>3} converted, {:>3} errors'.format(total, total-count-error, count, error))
    return error == 0

def data_task(v, name, base, outpath, extra, if_newer=True, extra_inpath=None, onlyx=False):
    msg('{:<3}: begin {} ...'.format(v, name.upper()))
    os.chdir(orig_dir)
    os.chdir(base)
    inpath = '{}.py'.format(name)
    good = True
    if not onlyx:
        if os.path.exists(outpath) and if_newer and os.path.getmtime(outpath) >= os.path.getmtime(inpath) \
            and (extra_inpath == None or
                os.path.exists(outpath) and if_newer and os.path.getmtime(outpath) >= os.path.getmtime(extra_inpath) \
            ):
            msg('Skipped, because result is up to date: {}'.format(outpath))
        else:
            with open(inpath) as f:
                version = v
                exec(f.read(), locals())
            if extra != None:
                this_good = extra()
                if not this_good:
                    msg('ERROR in executing subsequent actions: quitting!')
                    good = False
    else:
        this_good = extra(net=net)
        if not this_good:
            msg('ERROR in executing subsequent actions: quitting!')
            good = False
    os.chdir(orig_dir)
    msg('{:<3}: end   {} ...'.format(v, name.upper()))
    return good

def get_data_dir(source, version):
    API = fabric.load('{}{}'.format(source, version), '--', 'xxx', {"features": ('','')}, verbose='SILENT')
    return (API['data_dir'], API['my_file']('')[0:-5])

def do_all(excl=None, force=False, net=True, mysql=True, clean=False, commit_msg='fixes'):
    print(sys.argv)
    global orig_dir
    reset_time()
    orig_dir = os.getcwd()
    msg('starting in {}'.format(orig_dir))
    good = False
    for y in [1]:
        # source and version independent things
        for x in [1]:
            if excl != None and 'featuredoc' not in excl: 
                if not featuredoc(net=net, clean=clean): continue
            if excl != None and 'nb_html' not in excl: 
                if not make_snapshots('html'): continue
            if excl != None and 'nb_python' not in excl:
                if not make_snapshots('python'): continue
            good = True
        if not good: continue

        # source and version dependent things
        source = 'etcbc'

        for v in versions.strip().split():
            if not good: continue
            good = False

            (data_dir, output_dir) = get_data_dir(source, v)
            phono_output = '{}/ph/phono.{}{}'.format(data_dir, source, v)
            lexicon_output = '{}/{}{}/annotations/lexicon/_header_.xml'.format(data_dir, source, v)
            passage_sql = '{}/shebanq/shebanq_passage{}.sql'.format(output_dir, v)

            def to_db():
                os.chdir(output_dir)
                this_good = False
                for x in [1]:
                    msg('START Importing into MYSQL: {}'.format(passage_sql))
                    if mysql:
                        if subprocess.call('mysql -u root < {}'.format(passage_sql), shell=True): continue 
                        msg('OK Importing into MYSQL: {}'.format(passage_sql))
                    else:
                        msg('Skipped because of mysql=False')
                    msg('START sending to server: {}'.format(passage_sql))
                    if net:
                        if subprocess.call('scp -r {} {}@{}:{}'.format(
                            passage_sql, server_user, server, server_path), shell=True): continue
                        msg('DONE sending to server: {}'.format(passage_sql))
                    else:
                        msg('Skipped because of net=False')
                    this_good = True
                return this_good

            for x in [1]:
                if excl != None and 'phono' not in excl:
                    if not data_task(
                        v,
                        'phono', 'tools/phono', phono_output,
                        None,
                        if_newer=not force,
                    ): continue
                if excl != None and 'lexicon' not in excl:
                    if not data_task(
                        v,
                        'lexicon', 'tools/shebanq', lexicon_output,
                        None,
                        if_newer=not force,
                        extra_inpath=phono_output,
                    ): continue
                if excl != None and 'laf2shebanq' not in excl:
                    if not data_task(
                        v,
                        'laf2shebanq', 'tools/shebanq', passage_sql,
                        to_db,
                        if_newer=force,
                        extra_inpath=lexicon_output,
                        onlyx=False,
                    ): continue
                good = True

        if not good: continue

        # source and version independent things
        for x in [1]:
            if excl != None and 'shebanq' not in excl: 
                if not shebanq(commit_msg, net=net): continue
            good = True
        if not good: continue

    if not good:
        msg('There were errors')
    else:
        msg('All commands completed succesfully')

good = do_all(
    force=False,
    net=False,
    mysql=False,
    clean=False,
    commit_msg='small fixes',
    excl={
#   'shebanq',
    'featuredoc',
    'nb_html',
    'nb_python',
    'phono',
    'lexicon',
    'laf2shebanq',
    },
)
