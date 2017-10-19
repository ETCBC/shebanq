# Here are the emdros versions that have been used.
# The last one is the current version

emdros_versions = [
    'emdros 3.4.0',
    '3.4.1.pre12',
    'emdros 3.5.3',
]
# copied manually from /opt/emdros/include/emdros/version-emdros.h
config = dict(shebanq_user='shebanq')
config_path = '/opt/emdros/cfg/mql.cfg'
with open(config_path) as p:
    config['shebanq_passwd'] = p.read().rstrip('\n')
config_path = '/opt/emdros/cfg/host.cfg'
with open(config_path) as p:
    config['shebanq_host'] = p.read().rstrip('\n')
