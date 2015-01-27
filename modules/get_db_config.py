config = dict(shebanq_user='shebanq', shebanq_host='localhost')
config_path = '/opt/emdros/cfg/mql.cfg'
with open(config_path) as p:
    config['shebanq_passwd'] = p.read().rstrip('\n')
