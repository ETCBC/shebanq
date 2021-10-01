#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to restore a shebanq server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options]

Restores databases that collect dynamic website data of SHEBANQ:

*   shebanq_web
*   shebanq_note

You can get a recent backup on the server by means of provision.sh
"

showusage "$1" "$USAGE"

setsituation "$HOSTNAME" "Restoring data on" "$USAGE"

ensuredir "$UNPACK"

sudo -n /usr/bin/systemctl stop httpd.service

# order of dropping and creating is important!

echo "unzipping database dumps for shebanq_web and shebanq_note"
cp $TARGET/shebanq_web.sql.gz $UNPACK
cp $TARGET/shebanq_note.sql.gz $UNPACK
gunzip -f $UNPACK/shebanq_web.sql.gz
gunzip -f $UNPACK/shebanq_note.sql.gz
echo "dropping and creating databases shebanq_web and shebanq_note"
mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e 'drop database if exists shebanq_note;'
mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e 'drop database if exists shebanq_web;'
mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e 'create database shebanq_web;'
mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e 'create database shebanq_note;'
echo "loading databases shebanq_web and shebanq_note"
echo "use shebanq_web" | cat - $UNPACK/shebanq_web.sql | mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt
echo "use shebanq_note" | cat - $UNPACK/shebanq_note.sql | mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt
sleep 2

sudo -n /usr/bin/systemctl start httpd.service

erasedir "$UNPACK"
