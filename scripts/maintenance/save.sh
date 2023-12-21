#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to save backup from a server to local server
# Run it on your local computer.

if [[ ! -e "${0%/*}/config.sh" ]]; then
    echo "No config.sh found
Probably you are running this script from the maintenance directory.
You should run it from the _local directory where you have your
localized config.sh.

Hint: do

./localize.sh
cd ../../_local
    "
    exit
fi

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh


USAGE="
Usage: ./$(basename $0) situation

Saves the latest backup from a $APP server to a local server.

N.B. The backup must already have been made on the server itself by means
of the backup.sh script.

situation:
    p:   save from the current production server
    pn:  save from the new production server
    t:   save from the test server
    o:   save from the current other server
    on:  save from the new other server
"

showUsage "$1" "$USAGE"

setSituation "$1" "Saving latest backup from" "$USAGE"
shift

if [[ "$1" == --* ]]; then
    echo "Unrecognized switch: $1"
    echo "Do ./$(basename $0) --help for available options"
    exit
fi

latestSrcDir="$SERVER_BACKUP_DIR/latest"
if [[ "$situation" == "t" || "$situation" == "pn" || "$situation" == "on" ]]; then
    backupDir="$BACKUP_ALT_DIR"
else
    backupDir="$BACKUP_DIR"
fi

latestDstDir="$backupDir/latest"

if [[ -e "$latestDstDir" ]]; then
    rm -rf "$latestDstDir"
fi
if [[ -L "$latestDstDir" ]]; then
    rm "$latestDstDir"
fi


scp -r "$SERVER_USER@$SERVER:$latestSrcDir" "$backupDir/"
cd "$latestDstDir"

backupDatetime=`cat stamp`

echo "Renaming incoming set to $backupDatetime"

cd "$backupDir"
if [[ -e "$backupDatetime" ]]; then
    rm -rf "$backupDatetime"
fi

mv latest "$backupDatetime"
ln -s "$backupDatetime" latest

echo "Saved under $backupDir"
