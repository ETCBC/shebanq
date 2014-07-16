import logging
import os
from ConfigParser import SafeConfigParser


class Configuration():

    def __init__(self):
        parser = SafeConfigParser()
        logging.debug("Trying to find the configuration file for shebanq_db.passage")
        c_path = ['/usr/local/shebanq/shebanq_db.cfg', 'shebanq_db.cfg']
        logging.debug("Trying these locations: " + str(c_path))
        for path in c_path:
            if os.path.isfile(path):
                break
        if not os.path.isfile(path):
            logging.error("No configuration file found in locations " + str(c_path))
            raise Exception("No configuration file found in locations " + str(c_path))

        logging.info("Trying to configure shebanq_db.passage with configuration found at " + path)
        try:
            parser.read(path)
            self.passage_host = parser.get('passage', 'host')
            self.passage_user = parser.get('passage', 'user')
            self.passage_passwd = parser.get('passage', 'passwd')
            self.passage_db = parser.get('passage', 'db')
        except:
            logging.error("A correct configuration file is expected at " + path)
        try:
            parser.read(path)
            self.shebanq_host = parser.get('shebanq', 'host')
            self.shebanq_user = parser.get('shebanq', 'user')
            self.shebanq_passwd = parser.get('shebanq', 'passwd')
            self.shebanq_db = parser.get('shebanq', 'db')
        except:
            logging.error("A correct configuration file is expected at " + path)
