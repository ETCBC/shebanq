#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to save backup from a server to local server
# Run it on your local computer.

source ${0%/*}/config.sh


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
