#!/bin/bash
# This a the script that you can run on the production server of SHEBANQ to update the code and the data

# run it as follows:
#
# ./updateData.sh version what
#
# where what p or m or nothing
# 
# If nothing: do passage db and mql db
# if p: do passage db only
# if m: do mql db only
#
# This script is set up to work at specific servers.
# Currently it supports 
#   clarin11.dans.knaw.nl (SELINUX)
#   PPJV003 (Ubuntu) (default)

# MYSQL_PDIR: directory with config files for talking with mysql
# SH_ADIR   : directory where the web app shebanq resides (and also web2py itself)
# INCOMING  : directory where installation files arrive
# UNPACK    : directory where installation files are unpacked

INCOMING="/home/dirkr/shebanq-install"

if [ "$HOSTNAME" == "PPJV003" ]; then
        ON_LWEB=1
        MYSQL_PDIR="/root"
        SH_ADIR="/home/www-data"
        MQL_OPTS="-u root"
        UNPACK="/home/dirkr/shebanq-unpack"
fi
if [ "$HOSTNAME" == "clarin11.dans.knaw.nl" ]; then
        ON_CLARIN=1
        MYSQL_PDIR="/opt/emdros/cfg"
        SH_ADIR="/opt/web-apps"
        MQL_OPTS="-u shebanq_admin -h mysql11.dans.knaw.nl"
        UNPACK="/data/shebanq/unpack"
fi

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl stop httpd.service
else
    service apache2 stop
fi

cd $SH_ADIR/shebanq
mkdir -p $UNPACK

if [ "$1" == "" ]; then
    echo "No version specified. Abort"
else
    VERSION="$1"
    KIND="$2"
    if [ "$KIND" == "" ] || [ "$KIND" == "m" ]; then
        DBNAME="shebanq_etcbc$VERSION"
        echo "unzipping $DBNAME"
        cp $INCOMING/$DBNAME.mql.bz2 $UNPACK
        bunzip2 -f $UNPACK/$DBNAME.mql.bz2
        echo "dropping $DBNAME"
        mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e "drop database if exists $DBNAME;"
        echo "importing $DBNAME"
        mql -n -b m -p `cat $MYSQL_PDIR/mqlimportopt` $MQL_OPTS -e UTF8 < $UNPACK/$DBNAME.mql
    fi

    if [ "$KIND" == "" ] || [ "$KIND" == "p" ]; then
        PDBNAME="shebanq_passage$VERSION"
        echo "unzipping $PDBNAME"
        cp $INCOMING/$PDBNAME.sql.gz $UNPACK
        gunzip -f $UNPACK/$PDBNAME.sql.gz
        echo "loading $PDBNAME"
        mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt < $UNPACK/$PDBNAME.sql
        echo "Done"
    fi
fi

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl start httpd.service
else
    service apache2 start
fi

