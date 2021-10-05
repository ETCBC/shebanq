#!/bin/bash

cd -- "$(dirname "$BASH_SOURCE")"

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Starts SHEBANQ local webserver.
"

showUsage "$1" "$USAGE"

cd "$SERVER_APP_DIR"
./visit.sh &

cd "$SERVER_APP_DIR/web2py"

python3 web2py.py --no_gui -s localhost -p 8100 -a demo -c local.crt -k local.key
