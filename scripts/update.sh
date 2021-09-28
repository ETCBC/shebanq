#!/bin/bash
# This a the script that you can run on the acceptation/production server of SHEBANQ to update the code and the data

# run it as follows:
#
# ./update.sh                            # if only code or docs has changed
# ./update.sh -d   version               # if there are changes in the passage databases
# ./update.sh -de  version               # if there are changes in the emdros databases
#
# -de includes the actions for -d and that includes the actions for no arguments.

# This script is set up to work at specific servers.
# Currently it supports 
#   clarin31.dans.knaw.nl (SELINUX, production)
#   tclarin31.dans.knaw.nl (SELINUX, staging)

# MYSQL_PDIR: directory with config files for talking with mysql
# APP_DIR   : directory where the web app shebanq resides (and also web2py itself)
# INCOMING  : directory where installation files arrive
# UNPACK    : directory where installation files are unpacked

TOPLEVEL="/home/dirkr"
INCOMING="/home/dirkr/shebanq-install"
MYSQL_PDIR="/opt/emdros/cfg"
APP_DIR="/opt/web-apps"
WEB2PY_DIR="$APP_DIR/web2py"
SHEBANQ_DIR="$APP_DIR/shebanq"
UNPACK="/data/shebanq/unpack"

# put the next setting to "x" if your production machine does not already have data
PRODUCTION_HAS_DATA="v"

if [ "$HOSTNAME" == "clarin31.dans.knaw.nl" ]; then
    echo "Updating PRODUCTION machine ..."
    PRODUCTION="v"
    MQL_OPTS="-u shebanq_admin -h mysql11.dans.knaw.nl"
elif [ "$HOSTNAME" == "tclarin31.dans.knaw.nl" ]; then
    echo "Updating STAGING machine ..."
    PRODUCTION="x"
    MQL_OPTS="-u shebanq_admin"
else
    echo "Update not supported on machine $HOSTNAME"
    exit
fi

sudo -n /usr/bin/systemctl stop httpd.service
if [ "$PRODUCTION" == "x" || "$PRODUCTION_HAS_DATA" == "x" ]; then
    sudo -n /usr/bin/systemctl stop mariadb.service
fi

echo "Updating shebanq ..."
cd $SHEBANQ_DIR
echo "- Pull from github..."
git pull origin master
echo "- Done pulling."
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

# the following script creates a logging.conf in the web2py directory.
# This file must be removed before the webserver starts up, otherwise httpd wants to write web2py.log, which is generally not allowed
# and especially not under linux.
# Failing to remove this file will result in an Internal Server Error by SHEBANQ!
cd $WEB2PY_DIR
echo "- Remove sessions ..."
python3 web2py.py -Q -S shebanq -M -R scripts/sessions2trash.py -A -o -x 600000

sleep 1

cd $SHEBANQ_DIR
mkdir -p "$UNPACK"

if [ "$1" == "-de" ]; then
    if [ "$2" == "" ]; then
        echo "No version specified. Abort"
    else
        VERSION="$2"
        DBNAME="shebanq_etcbc$VERSION"
        echo "unzipping $DBNAME"
        cp $INCOMING/$DBNAME.mql.bz2 $UNPACK
        bunzip2 -f $UNPACK/$DBNAME.mql.bz2
        echo "dropping $DBNAME"
        mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e "drop database if exists $DBNAME;"
        echo "importing $DBNAME"
        mql -n -b m -p `cat $MYSQL_PDIR/mqlimportopt` $MQL_OPTS -e UTF8 < $UNPACK/$DBNAME.mql
    fi
fi
if [ "$1" == "-d" -o "$1" == "-de" ]; then
    if [ "$2" == "" ]; then
        echo "No version specified. Abort"
    else
        VERSION="$2"
        PDBNAME="shebanq_passage$VERSION"
        echo "unzipping $PDBNAME"
        cp $INCOMING/$PDBNAME.sql.gz $UNPACK
        gunzip -f $UNPACK/$PDBNAME.sql.gz
        echo "loading $PDBNAME"
        mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt < $UNPACK/$PDBNAME.sql
    fi
fi

# Here we clean the logging.conf script as promised above.
cd $WEB2PY_DIR
if [ -e logging.conf ]; then
    rm logging.conf
fi

sleep 2

if [ "$PRODUCTION" == "x" || "$PRODUCTION_HAS_DATA" == "x" ]; then
    sudo -n /usr/bin/systemctl start mariadb.service
fi
sudo -n /usr/bin/systemctl start httpd.service
