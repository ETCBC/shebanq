#!/bin/bash
# This a the script that you can run on the production server of SHEBANQ to update the code and the data

# run it as follows:
#
# ./update.sh                              # if only code or docs has changed
# ./update.sh -d                           # if there are changes in the passage databases
# ./update.sh -de                          # if there are changes in the emdros databases
#
# -de includes the actions for -d and that includes the actions for no arguments.

# This script is set up to work at specific servers.
# Currently it supports 
#   clarin11.dans.knaw.nl (SELINUX)
#   PPJV003 (Ubuntu) (default)

# MYSQL_PDIR: directory with config files for talking with mysql
# SH_ADIR   : directory where the web app shebanq resides (and also web2py itself)

if [ "$HOSTNAME" == "PPJV003" ]; then
        ON_LWEB=1
        MYSQL_PDIR="/root"
        SH_ADIR="/home/www-data"
        MQL_OPTS="-u root"
fi
if [ "$HOSTNAME" == "clarin11.dans.knaw.nl" ]; then
        ON_CLARIN=1
        MYSQL_PDIR="/opt/emdros/cfg"
        SH_ADIR="/opt/web-apps"
        MQL_OPTS="-u shebanq_admin -h mysql11.dans.knaw.nl"
fi

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl stop httpd.service
else
    service apache2 stop
fi

cd $SH_ADIR/shebanq
git pull origin master
cd $SH_ADIR/web2py
python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
cd $SH_ADIR/shebanq
if [ $ON_LWEB ]; then
    cp -R /usr/local/lib/python2.7/dist-packages/guppy modules
    chown -R www-data:www-data /home/www-data/web2py
    chown -R www-data:www-data /home/www-data/shebanq
fi
sleep 1

cd $SH_ADIR/shebanq
if [ "$1" == "-de" ]; then
    echo "dropping etcbc database version 4"
    mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'drop database if exists shebanq_etcbc4;'
    echo "dropping etcbc database version 4b"
    mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt -e 'drop database if exists shebanq_etcbc4b;'
    echo "unzipping etcbc database dump for version 4"
    bunzip2 -f -k /home/dirkr/shebanq-install/x_etcbc4.mql.bz2
    echo "unzipping etcbc database dump for version 4b"
    bunzip2 -f -k /home/dirkr/shebanq-install/x_etcbc4b.mql.bz2
    echo "importing etcbc database for version 4"
    mql -n -b m -p `cat $MYSQL_PDIR/mqlimportopt` $MQL_OPTS -e UTF8 < /home/dirkr/shebanq-install/x_etcbc4.mql
    echo "importing etcbc database for version 4b"
    mql -n -b m -p `cat $MYSQL_PDIR/mqlimportopt` $MQL_OPTS -e UTF8 < /home/dirkr/shebanq-install/x_etcbc4b.mql
fi
if [ "$1" == "-d" -o "$1" == "-de" ]; then
    echo "unzipping passage database for version 4"
    gunzip -f /home/dirkr/shebanq-install/shebanq_passage4.sql.gz
    echo "loading passage database for version 4"
    mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4.sql
    echo "unzipping passage database for version 4b"
    gunzip -f /home/dirkr/shebanq-install/shebanq_passage4b.sql.gz
    echo "loading passage database for version 4b"
    mysql --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4b.sql
fi
sleep 2

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl start httpd.service
else
    service apache2 start
fi

