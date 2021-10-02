#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to restore a server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0)

Restores databases that collect dynamic website data of SHEBANQ:

*   $DYNAMIC_WEB
*   $DYNAMIC_NOTE

You can get a recent backup on the server by means of provision.sh
"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Restoring data on" "$USAGE"

ensureDir "$SERVER_UNPACK_DIR"

sudo -n /usr/bin/systemctl stop httpd.service

# order of dropping and creating is important!

echo "unzipping database dumps for $DYNAMIC_WEB and $DYNAMIC_NOTE"
cp $SERVER_INSTALL_DIR/$DYNAMIC_WEB.sql.gz $SERVER_UNPACK_DIR
cp $SERVER_INSTALL_DIR/$DYNAMIC_NOTE.sql.gz $SERVER_UNPACK_DIR
gunzip -f $SERVER_UNPACK_DIR/$DYNAMIC_WEB.sql.gz
gunzip -f $SERVER_UNPACK_DIR/$DYNAMIC_NOTE.sql.gz
echo "dropping and creating databases $DYNAMIC_WEB and $DYNAMIC_NOTE"
mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e 'drop database if exists $DYNAMIC_NOTE;'
mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e 'drop database if exists $DYNAMIC_WEB;'
mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e 'create database $DYNAMIC_WEB;'
mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e 'create database $DYNAMIC_NOTE;'
echo "loading databases $DYNAMIC_WEB and $DYNAMIC_NOTE"
echo "use $DYNAMIC_WEB" | cat - $SERVER_UNPACK_DIR/$DYNAMIC_WEB.sql | mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt
echo "use $DYNAMIC_NOTE" | cat - $SERVER_UNPACK_DIR/$DYNAMIC_NOTE.sql | mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt
sleep 2

sudo -n /usr/bin/systemctl start httpd.service

eraseDir "$SERVER_UNPACK_DIR"
