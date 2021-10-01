#!/bin/bash

# Script to backup a SHEBANQ server.
# Run it on the server.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options]

Backs up databases that collect dynamic website data of SHEBANQ:

*   shebanq_web
*   shebanq_note

The backsup will be protected against access from others.
They end up in directory backups/yyyy-mm-ddThh-mm-ss, where the last part is the
datetime when the backup has been made.
"

showusage "$1" "$USAGE"

setscenario "$HOSTNAME" "Backing up" "$USAGE"

backupdatetime=`date +"%Y-%m-%dT%H-%M-%S"`
BUDIR="$TARGETBUDIR/$backupdatetime"
LATESTDIR="$TARGETBUDIR/latest"

ensuredir "$BUDIR"

sudo -n /usr/bin/systemctl stop httpd.service

echo "creating database dumps for shebanq_web and shebanq_note in $BUDIR"
for db in shebanq_web shebanq_note
do
    bufl="$BUDIR/$db.sql.gz"
    mysqldump --defaults-extra-file=$CFG_DIR/mysqldumpopt $db | gzip > "$bufl"
done
echo "$backupdatetime" > "$BUDIR/stamp"
chown -R $TARGETUSER:$TARGETUSER "$BUDIR"
chmod -R go-rwx "$BUDIR"

if [[ -e "$LATESTDIR" ]]; then
    rm -rf "$LATESTDIR"
fi
ln -s "$BUDIR" "$LATESTDIR"
chown -R $TARGETUSER:$TARGETUSER "$LATESTDIR"
chmod -R go-rwx "$LATESTDIR"

sleep 1

sudo -n /usr/bin/systemctl start httpd.service
