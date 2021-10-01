#!/bin/bash

# Script to restore user data of a SHEBANQ server.
# Run it on that server.
# The server must have been provisioned.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: $(basename $0) [Options]

Restores databases that collect dynamic website data of SHEBANQ:

*   shebanq_web
*   shebanq_note
"

showusage "$usage"

setscenario "$HOSTNAME" "Restoring data on" "$USAGE"

if [[ -f "$UNPACK" ]]; then
    rm -rf "$UNPACK"
fi
if [[ ! -d "$UNPACK" ]]; then
    mkdir -p "$UNPACK"
fi

sudo -n /usr/bin/systemctl stop httpd.service

# order of dropping and creating is important!

echo "unzipping database dumps for shebanq_web and shebanq_note"
cp $TARGET/shebanq_web.sql.gz $UNPACK
cp $TARGET/shebanq_note.sql.gz $UNPACK
gunzip -f $UNPACK/shebanq_web.sql.gz
gunzip -f $UNPACK/shebanq_note.sql.gz
echo "dropping and creating databases shebanq_web and shebanq_note"
mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'drop database if exists shebanq_note;'
mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'drop database if exists shebanq_web;'
mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'create database shebanq_web;'
mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'create database shebanq_note;'
echo "loading databases shebanq_web and shebanq_note"
echo "use shebanq_web" | cat - $UNPACK/shebanq_web.sql | mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt
echo "use shebanq_note" | cat - $UNPACK/shebanq_note.sql | mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt
sleep 2

sudo -n /usr/bin/systemctl start httpd.service
