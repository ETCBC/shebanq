#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0) [version]

Load static data into mysql.

version:
    a valid SHEBANQ data version, such as 4, 4b, c, 2017, 2021
    It will restrict the data provisioning to the databases
    that belong to this version.
    If left out, all versions will be done.
"

showUsage "$1" "$USAGE"

if [[ "$1" == "" ]]; then
    versions="$STATIC_VERSIONS"
else
    versions="$1"
    shift
fi

# static data

echo "o-o-o    LOAD STATIC DATA start    o-o-o"

mysqlOpt="-u root"

ensureDir ~/tmp
cd ~/tmp

for version in $versions
do
    echo "o-o-o - VERSION $version passage"
    db="$STATIC_PASSAGE$version"
    echo "o-o-o - unzipping $db"
    cp "$sourceRepo/$version/$db.sql.gz" .
    gunzip -f "$db.sql.gz"
    echo "o-o-o - loading $db (may take half a minute)"
    mysql $mysqlOpt < "$db.sql"
    rm $db.sql

    echo "o-o-o - VERSION $version emdros"
    db="$STATIC_ETCBC$version"
    echo "o-o-o - unzipping $db"
    cp $sourceRepo/$version/$db.mql.bz2 .
    bunzip2 -f $db.mql.bz2
    echo "o-o-o - dropping $db"
    mysql $mysqlOpt -e "drop database if exists $db;"
    echo "o-o-o - importing $db (may take a minute or two)"
    mqlOpt="-e UTF8 -n -b m $mysqlOpt"
    mql $mqlOpt < $db.mql
    rm $db.mql
done
