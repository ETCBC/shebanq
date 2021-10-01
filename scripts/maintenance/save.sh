#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to save backup from a shebanq server to local machine
# Run it on your local computer.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) situation

Saves the latest backup from a shebanq server to a local machine.

N.B. The backup must already have been made on the server itself by means
of the backup.sh script.

situation:
    p:   save from the current production machine
    pn:  save from the current production machine
    t:   save from the test machine
    o:   save from the other machine
"

showusage "$1" "$USAGE"

setsituation "$1" "Saving latest backup from" "$USAGE"
shift

LATESTSRCDIR="$TARGETBUDIR/latest"
LATESTDSTDIR="$BACKUPDIR/latest"

if [[ -e "$LATESTDSTDIR" ]]; then
    rm -rf "$LATESTDSTDIR"
fi

scp -r "$TARGETUSER@$MACHINE:$LATESTSRCDIR" "$BACKUPDIR/"
cd "$LATESTDSTDIR"
backupdatetime=`cat stamp`
echo "Latest back up made at $backupdatetime"

cd "$BACKUPDIR"
if [[ -e "$backupdatetime" ]]; then
    rm -rf "$backupdatetime"
fi

echo "renaming incoming set to $budatetime"

mv latest "$backupdatetime"

echo "linking latest to $budatetime"
ln -s "$backupdatetime" latest

echo "Saved under $BACKUPDIR"
