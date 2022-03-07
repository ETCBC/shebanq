#!/bin/sh

mysql -h«DB_HOST» -uroot < «SERVER_CFG_DIR»/user.sql
mysql -h«DB_HOST» -uroot < «SERVER_CFG_DIR»/grants.sql

mysqlOpt="--defaults-extra-file=«SERVER_CFG_DIR»/mysqldumpopt"

for version in «STATIC_VERSIONS»
do
    echo "o-o-o - VERSION $version «STATIC_PASSAGE»"
    db="«STATIC_PASSAGE»$version"
    datafile="${db}.sql"
    echo "o-o-o - unzipping $db"
    gunzip -f "${db}.gz"
    echo "o-o-o - loading $db (may take half a minute)"
    mysql ${mysqlOpt} < ${datafile}
    rm ${datafile}

    echo "o-o-o - VERSION $version «STATIC_ETCBC»"
    db="«STATIC_ETCBC»$version"
    datafile="${db}.mql"
    echo "o-o-o - unzipping $db"
    bunzip2 -f ${datafile}.bz2
    mysql ${mysqlOpt} -h«DB_HOST» -e "drop database if exists ${db};"
    «SERVER_MQL_DIR»/mql -e UTF8 -n -b m -h «DB_HOST» -u shebanq_admin -p uvw456 < ${datafile}
    rm ${datafile}
done
