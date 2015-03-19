config = dict(shebanq_user='shebanq')
config_path = '/opt/emdros/cfg/mql.cfg'
with open(config_path) as p:
    config['shebanq_passwd'] = p.read().rstrip('\n')
config_path = '/opt/emdros/cfg/host.cfg'
with open(config_path) as p:
    config['shebanq_host'] = p.read().rstrip('\n')
