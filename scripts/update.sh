#!/bin/bash

# Script to update a shebanq server.
# Run it on the server.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options]

Without options, it only updates the shebanq software.
The shebanq server must be fully installed.

By means of options, you can also perform data updates.

Options:

    -d version: update mysql data (passage databases)
    -de version: update mysql data and emdros data (etcbc databases)

    where version is a valid SHEBANQ version.
    Only the indicated dataversion will be imported.
"

showusage "$1" "$USAGE"

setscenario "$HOSTNAME" "Updating" "$USAGE"

ensuredir "$UNPACK"

MQL_OPTS="-u shebanq_admin $DBHOST"

# stop Apache and if needed the database

sudo -n /usr/bin/systemctl stop httpd.service
if [[ "DBHOST" == "" ]]; then
    sudo -n /usr/bin/systemctl stop mariadb.service
fi

# pull updates to shebanq code

echo "Updating shebanq ..."
cd $SHEBANQ_DIR
echo "- Pull from github..."
git fetch origin
git checkout master
git reset --hard origin/master
echo "- Done pulling."

# compile all python code

cd $WEB2PY_DIR
echo "- Compile admin app ..."
python3 -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/admin')"
echo "- Compile shebanq app ..."
python3 -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
echo "- Compile modules of admin app ..."
cd applications/admin
python3 -m compileall modules
echo "- Compile modules of shebanq app ..."
cd $SHEBANQ_DIR
python3 -m compileall modules
# chown apache:apache $WEB2PY_DIR/welcome.w2p
echo "- Done compiling."

# Import a new or updated data version if needed

cd $SHEBANQ_DIR
mkdir -p "$UNPACK"

if [[ "$1" == "-d" || "$1" == "-de" ]]; then
    if [[ "$2" == "" ]]; then
        echo "No version specified. Abort"
    else
        VERSION="$2"
        PASSAGEDB="shebanq_passage$VERSION"

        if [[ "$1" == "-de" ]]; then
            EMDROSDB="shebanq_etcbc$VERSION"
            echo "unzipping $EMDROSDB"
            cp $INCOMING/$EMDROSDB.mql.bz2 $UNPACK
            bunzip2 -f $UNPACK/$EMDROSDB.mql.bz2
            echo "dropping $EMDROSDB"
            mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "drop database if exists $EMDROSDB;"
            echo "importing $EMDROSDB"
            mql -n -b m -p `cat $CFG_DIR/mqlimportopt` $MQL_OPTS -e UTF8 < $UNPACK/$EMDROSDB.mql
        fi

        echo "unzipping $PASSAGEDB"
        cp $TARGET/$PASSAGEDB.sql.gz $UNPACK
        gunzip -f $UNPACK/$PASSAGEDB.sql.gz
        echo "loading $PASSAGEDB"
        mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt < $UNPACK/$PASSAGEDB.sql
    fi
fi

sleep 2

# start database if needed

if [[ "DBHOST" == "" ]]; then
    sudo -n /usr/bin/systemctl start mariadb.service
fi

# the following step creates a logging.conf in the web2py directory.
# This file must be removed before the webserver starts up,
# otherwise httpd wants to write web2py.log,
# which is generally not allowed and especially not under linux.
# Failing to remove this file will result in
# an Internal Server Error by SHEBANQ!

cd $WEB2PY_DIR
echo "- Remove sessions ..."
python3 web2py.py -S shebanq -M -R scripts/sessions2trash.py -A -o -x 600000

if [[ -e logging.conf ]]; then
    rm logging.conf
fi

sleep 1

# start Apache

sudo -n /usr/bin/systemctl start httpd.service

erasedir "$UNPACK"
