#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to backup a SHEBANQ server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0)

Backs up databases that collect dynamic website data of SHEBANQ:

*   $DYNAMIC_WEB
*   $DYNAMIC_NOTE

The backsup will be protected against access from others.
They end up in directory backups/yyyy-mm-ddThh-mm-ss, where the last part is the
datetime when the backup has been made.
"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Backing up" "$USAGE"

backupDatetime=`date +"%Y-%m-%dT%H-%M-%S"`
backupDir="$SERVER_BACKUP_DIR/$backupDatetime"
latestDir="$SERVER_BACKUP_DIR/latest"

ensureDir "$backupDir"

sudo -n /usr/bin/systemctl stop httpd.service

echo "creating database dumps for $DYNAMIC_WEB and $DYNAMIC_NOTE in $backupDir"
for db in $DYNAMIC_WEB $DYNAMIC_NOTE
do
    bufl="$backupDir/$db.sql.gz"
    mysqldump --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt $db | gzip > "$bufl"
done
echo "$backupDatetime" > "$backupDir/stamp"
chown -R $SERVER_USER:$SERVER_USER "$backupDir"
chmod -R go-rwx "$backupDir"

if [[ -e "$latestDir" ]]; then
    rm -rf "$latestDir"
fi
ln -s "$backupDir" "$latestDir"
chown -R $SERVER_USER:$SERVER_USER "$latestDir"
chmod -R go-rwx "$latestDir"

sleep 1

sudo -n /usr/bin/systemctl start httpd.service
