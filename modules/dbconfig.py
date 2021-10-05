import os

# Here are the emdros versions that have been used.
# The last one is the current version

EMDROS_VERSIONS = [
    "emdros 3.4.0",
    "3.4.1.pre12",
    "emdros 3.5.3",
    "emdros 3.7.3",
]
# copied manually from /opt/emdros/include/emdros/version-emdros.h

CONFIG = dict(shebanqUser="shebanq")

configPath = "/opt/cfg/mql.cfg"
if os.path.exists(configPath):
    with open(configPath) as p:
        CONFIG["shebanqPassword"] = p.read().rstrip("\n")
else:
    CONFIG["shebanqPassword"] = "localpwd"

configPath = "/opt/cfg/host.cfg"
if os.path.exists(configPath):
    with open(configPath) as p:
        CONFIG["shebanqHost"] = p.read().rstrip("\n")
else:
    CONFIG["shebanqHost"] = "localhost"
