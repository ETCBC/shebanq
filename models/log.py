import logging

from gluon import current


logger = logging.getLogger("web2py.app.shebanq")
logger.setLevel(logging.WARN)
current.logger = logger
