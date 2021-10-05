#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Fetches GitHub repositories and shifts data around on the file system.
"

showUsage "$1" "$USAGE"

# clone or pull repositories bhsa and shebanq and web2py

ensureDir "$githubBase/etcbc"
ensureDir "$githubBase/web2py"
fetchRepo etcbc shebanq
fetchRepo etcbc bhsa
fetchRepo web2py web2py --recursive

installRepo etcbc shebanq
installRepo web2py web2py
