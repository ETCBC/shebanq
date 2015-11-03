#!/bin/bash
# This a the script that you can run on the production server of SHEBANQ to update the code and the data

# run it as follows:
#
# ./update.sh                              # if only code or docs has changed
# ./update.sh -d                           # if there are changes in the passage databases
# ./update.sh -de                          # if there are changes in the emdros databases
#
# -de includes the actions for -d and that includes the actions for no arguments.

service apache2 stop

git pull origin master
cd /home/www-data/web2py
python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
cd /home/www-data/shebanq
cp -R /usr/local/lib/python2.7/dist-packages/guppy modules
chown -R www-data:www-data /home/www-data/web2py
chown -R www-data:www-data /home/www-data/shebanq
sleep 1

cd /home/www-data/shebanq
if [ "$1" == "-de" ]; then
    echo "dropping etcbc database version 4"
    mysql --defaults-extra-file=/root/mysqldumpopt -e 'drop database if exists shebanq_etcbc4;'
    echo "dropping etcbc database version 4b"
    mysql --defaults-extra-file=/root/mysqldumpopt -e 'drop database if exists shebanq_etcbc4b;'
    echo "unzipping etcbc database dump for version 4"
    bunzip2 -f -k /home/dirkr/shebanq-install/x_etcbc4.mql.bz2
    echo "unzipping etcbc database dump for version 4b"
    bunzip2 -f -k /home/dirkr/shebanq-install/x_etcbc4b.mql.bz2
    echo "importing etcbc database for version 4"
    mql -n -b m -u root -p `cat /root/mqlimportopt` -e UTF8 < /home/dirkr/shebanq-install/x_etcbc4.mql
    echo "importing etcbc database for version 4b"
    mql -n -b m -u root -p `cat /root/mqlimportopt` -e UTF8 < /home/dirkr/shebanq-install/x_etcbc4b.mql
fi
if [ "$1" == "-d" -o "$1" == "-de" ]; then
    echo "unzipping passage database for version 4"
    gunzip -f /home/dirkr/shebanq-install/shebanq_passage4.sql.gz
    echo "loading passage database for version 4"
    mysql --defaults-extra-file=/root/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4.sql
    echo "unzipping passage database for version 4b"
    gunzip -f /home/dirkr/shebanq-install/shebanq_passage4b.sql.gz
    echo "loading passage database for version 4b"
    mysql --defaults-extra-file=/root/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4b.sql
fi
sleep 2
service apache2 start
