#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Installs web2py and shebanq in it.
"

showUsage "$1" "$USAGE"

cd "$SERVER_APP_DIR/web2py"

cp "$SCRIPT_SRC_DIR/routes.py" .
for item in local.crt local.csr local.key
do
    cp "$SCRIPT_SRC_DIR/computer/$item" .
done

cd applications
if [[ -e "$APP" ]]; then
    rm -rf "$APP"
fi
ln -s "$sourceRepo" $APP

ensureDir "$SERVER_APP_DIR"
cd "$SERVER_APP_DIR"

for item in start.sh config.sh doconfig.sh functions.sh start.sh visit.sh
do
    cp "$SCRIPT_SRC_DIR/computer/$item" .
done

mv start.sh shebanq.command
