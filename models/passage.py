from get_db_config import config
import re

'''Passage dabatase'''
passage_db = DAL('mysql://{}:{}@{}/{}'.format(
    config['shebanq_user'],
    config['shebanq_passwd'],
    config['shebanq_host'],
    'passage',
), migrate_enabled=False)

