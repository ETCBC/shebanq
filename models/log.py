import logging

from gluon import current


logger = logging.getLogger("web2py.app.shebanq")
logger.setLevel(logging.DEBUG)
current.logger = logger
logger.debug("XXXXXXXXXXXXXX TEST XXXXXXXXXXXXXXXXXXX")
