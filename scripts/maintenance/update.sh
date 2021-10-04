#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to update a server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0)

Only updates the $APP software.
The $APP server must be fully installed.
"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Updating" "$USAGE"

# stop Apache

sudo -n /usr/bin/systemctl stop httpd.service

# pull updates to $REPO code

echo "Updating $APP ..."
cd $SERVER_APP_DIR/$APP
echo "- Pull from github..."
git fetch origin
git checkout master
git reset --hard origin/master
echo "- Done pulling."

# compile all python code

compileApp $APP

# the following step creates a logging.conf in the web2py directory.
# This file must be removed before the webserver starts up,
# otherwise httpd wants to write web2py.log,
# which is generally not allowed and especially not under linux.
# Failing to remove this file will result in
# an Internal Server Error by SHEBANQ!

cd $SERVER_APP_DIR/web2py
echo "- Remove sessions ..."
python3 web2py.py -S $APP -M -R scripts/sessions2trash.py -A -o -x 600000

if [[ -e logging.conf ]]; then
    rm logging.conf
fi

sleep 1

# start Apache

sudo -n /usr/bin/systemctl start httpd.service
