#!/bin/bash

# Script to backup user data of a SHEBANQ server.
# Run it on that server.
# The server must have been provisioned.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: $(basename $0) [Options]

Backs up databases that collect dynamic website data of SHEBANQ:

*   shebanq_web
*   shebanq_note
"

showusage "$usage"

setscenario "$HOSTNAME" "Backing up" "$USAGE"

sudo -n /usr/bin/systemctl stop httpd.service

echo "creating database dumps for shebanq_web and shebanq_note"
mysqldump --defaults-extra-file=$CFG_DIR/mysqldumpopt shebanq_web | gzip > $TARGET/shebanq_web.sql.gz
chmod go-rwx $TARGET/shebanq_web.sql.gz
mysqldump --defaults-extra-file=$CFG_DIR/mysqldumpopt shebanq_note | gzip > $TARGET/shebanq_note.sql.gz
chmod go-rwx $TARGET/shebanq_note.sql.gz

sleep 1

sudo -n /usr/bin/systemctl start httpd.service
