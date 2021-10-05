#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Loads empty dynamic data.

This needs to be done in order to define the data model
of the dynamic data.
"

showUsage "$1" "$USAGE"

# empty user data

echo "o-o-o load empty databases for saved queries and notes"

cd ~/tmp
for db in shebanq_web shebanq_note
do 
    cp "$SCRIPT_SRC_DIR/$db.sql.gz" .
    gunzip "$srcDir/$db.sql.gz"
    mysql -u root -e "drop database if exists $db;"
    mysql -u root -e "create database $db;"
    echo "use $db" | cat - $$db.sql | mysql -u root
done
