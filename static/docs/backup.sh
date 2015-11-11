#!/bin/bash
# This a the script that you can run on the production server of SHEBANQ to backup the shebanq_web and shebanq_note databases

# run it as follows:
#
# ./backup.sh                             # if only code or docs has changed

# This script is set up to work at specific servers.
# Currently it supports 
#   clarin11.dans.knaw.nl (SELINUX)
#   PPJV003 (Ubuntu) (default)

# MYSQL_PDIR: directory with config files for talking with mysql
# SH_ADIR   : directory where the web app shebanq resides (and also web2py itself)
# INCOMING  : directory where installation files arrive

INCOMING="/home/dirkr"

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

echo "creating database dumps for shebanq_web and shebanq_note"
mysqldump --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt shebanq_web | gzip > $INCOMING/shebanq_web.sql.gz
chmod go-rwx $INCOMING/shebanq_web.sql.gz
mysqldump --defaults-extra-file=$MYSQL_PDIR/mysqldumpopt shebanq_note | gzip > $INCOMING/shebanq_note.sql.gz
chmod go-rwx $INCOMING/shebanq_note.sql.gz

sleep 1

if [ $ON_CLARIN ]; then
    sudo -n /usr/bin/systemctl start httpd.service
else
    service apache2 start
fi

