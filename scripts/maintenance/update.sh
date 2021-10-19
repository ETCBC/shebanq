#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to update a server.
# Run it on the server.

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh


USAGE="
Usage: ./$(basename $0) [Options]

Updates the $APP software and only that.
The $APP server must be fully installed.
It cleans obsolete sessions.

Options:
    --thorough: empties the cache and makes a first visit

In a normal case, it does a non-disruptive update:

*   it updates the SHEBANQ code
*   it does a httpd restart
*   a first visit is triggered, to warm up the cache

When --thorough is passed the sequence is as follows:

*   httpd is stopped completely
*   SHEBANQ code is updated
*   the test controller is executed
*   httpd is started
*   a first visit is triggered, to warm up the cache
"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Updating" "$USAGE"

doThorough="x"

if [[ "$1" == "--thorough" ]]; then
    doThorough="v"
elif [[ "$1" == --* ]]; then
    echo "Unrecognized switch: $1"
    echo "Do ./$(basename $0) --help for available options"
    exit
fi

# stop Apache

if [[ "$doThorough" == "v" ]]; then
    echo "o-o-o Stopping Apache ..."
    sudo -n /usr/bin/systemctl stop httpd.service
fi

# just in case routes or parameters_443 (password hash) or wsgihandler
# have changed

cd $SERVER_APP_DIR/web2py

for pyFile in parameters_443.py routes.py logging.conf wsgihandler.py
do
    cp "$SERVER_INSTALL_DIR/$pyFile" .
    chown $SERVER_USER:shebanq "$pyFile"
    chcon -t httpd_sys_content_t "$pyFile"
done

# pull updates to $REPO code

fetchShebanq
installShebanq "x"

echo "o-o-o Remove sessions ..."
echo "- Remove sessions ..."

cd $SERVER_APP_DIR/web2py
python3 web2py.py -S $APP -M -R scripts/sessions2trash.py -A -o -x 600000
logFile="$SERVER_APP_DIR/$APP/log/debug.log"
if [[ -e "$logFile" ]]; then
    rm -rf "$logFile"
fi

# test the controller

if [[ "$doThorough" == "v" ]]; then
    echo "o-o-o Run test controller ..."
    testController
    chown $SERVER_USER:shebanq "$logFile"
fi

# (re) start Apache nad do post-update steps

if [[ "$doThorough" == "v" ]]; then
    echo "o-o-o Starting Apache ..."
    sudo -n /usr/bin/systemctl start httpd.service

else
    echo "o-o-o Restarting Apache ..."
    sudo -n /usr/bin/systemctl restart httpd.service
fi

# make a first visit to warm up cache
firstVisit

echo "o-o-o Update done."
