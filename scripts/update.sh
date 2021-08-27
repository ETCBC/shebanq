#!/bin/bash
# This a the script that you can run on the production server of SHEBANQ to update the code and the data

# run it as follows:
#
# ./update.sh                              # if only code or docs has changed
# ./update.sh -w                           # upgrade web2py
# ./update.sh -d   version                 # if there are changes in the passage databases
# ./update.sh -de  version                 # if there are changes in the emdros databases
#
# -de includes the actions for -d and that includes the actions for no arguments.

# This script is set up to work at specific servers.
# Currently it supports 
#   clarin11.dans.knaw.nl (SELINUX)

# MYSQL_PDIR: directory with config files for talking with mysql
# SH_ADIR   : directory where the web app shebanq resides (and also web2py itself)
# INCOMING  : directory where installation files arrive
# UNPACK    : directory where installation files are unpacked

INCOMING="/home/dirkr/shebanq-install"

if [ "$HOSTNAME" == "clarin11.dans.knaw.nl" ]; then
        ON_CLARIN=1
        MYSQL_PDIR="/opt/emdros/cfg"
        SH_ADIR="/opt/web-apps"
        MQL_OPTS="-u shebanq_admin -h mysql11.dans.knaw.nl"
        UNPACK="/data/shebanq/unpack"
fi

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl stop httpd.service
fi

# upgrade web2py if -w is given

if [ "$1" == "-w" ]; then
    echo "- Upgrading web2py ..."
    cd $SH_ADIR
    if [ -e sav ]; then
        rm -rf sav
    fi
    mkdir sav
    mkdir sav/applications
    for fl in parameters*.py routes.py applications/shebanq
    do
        echo "--- save $fl to sav"
        cp -P -f web2py/$fl sav/$fl
    done
    pushd web2py
    echo "--- getting web2py from GitHub ..."
    #git add --all .
    #git commit -m "before upgrade"
    git reset --hard
    git pull origin master
    echo "--- done"
    cp handlers/wsgihandler.py .
    chown dirkr:shebanq wsgihandler.py
    popd
    for fl in parameters.py routes.py applications/shebanq
    do
        echo "--- restore $fl from sav"
        cp -P sav/$fl web2py/$fl
    done
    echo "- Done Upgrading web2py ..."
fi

# end upgrade web2py

cd $SH_ADIR/shebanq
git pull origin master
cd $SH_ADIR/web2py
python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/admin')"
python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"

# the following script creates a logging.conf in the web2py directory.
# This file must be removed before the webserver starts up, otherwise httpd wants to write web2py.log, which is generally not allowed
# and especially not under linux.
# Failing to remove this file will result in an Internal Server Error by SHEBANQ!
python web2py.py -Q -S shebanq -M -R scripts/sessions2trash.py -A -o -x 600000

cd applications/admin
python -m compileall models modules
cd $SH_ADIR/shebanq
python -m compileall models modules
if [ $ON_CLARIN ]; then
    # chown dirkr:shebanq $SH_ADIR/web2py/web2py.log
    chown dirkr:shebanq $SH_ADIR/web2py/welcome.w2p
fi
sleep 1

cd $SH_ADIR/shebanq
mkdir -p $UNPACK

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
cd $SH_ADIR/web2py
if [ -e logging.conf ]; then
    rm logging.conf
fi

sleep 2

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl start httpd.service
fi

