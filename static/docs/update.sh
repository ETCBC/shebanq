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
cd /home/www-data/shebanq
if [ "$1" == "-f" ]; then
    echo clear cache
    rm -r cache
fi
if [ "$1" == "-de" ]; then
    echo "dropping etcbc database version 4"
    mysql --defaults-extra-file=/root/mysqldumpopt -e 'drop database if exists shebanq_etcbc4;'
    echo "dropping etcbc database version 4b"
    mysql --defaults-extra-file=/root/mysqldumpopt -e 'drop database if exists shebanq_etcbc4b;'
    echo "importing etcbc database for version 4"
    mql -b m -u root -p `cat mqlimportopt` -e UTF8 < /home/dirkr/shebanq-install/shebanq_etcbc4.sql
    echo "importing etcbc database for version 4b"
    mql -b m -u root -p `cat mqlimportopt` -e UTF8 < /home/dirkr/shebanq-install/shebanq_etcbc4b.sql
fi
if [ "$1" == "-d" || "$1" == "-de" ]; then
    echo "loading passage database for version 4"
    mysql --defaults-extra-file=/root/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4.sql
    echo "loading passage database for version 4b"
    mysql --defaults-extra-file=/root/mysqldumpopt < /home/dirkr/shebanq-install/shebanq_passage4b.sql
fi
git pull origin master
cd /home/www-data/web2py
python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
cd /home/www-data/shebanq
cp -R /usr/local/lib/python2.7/dist-packages/guppy modules
chown -R www-data:www-data /home/www-data/web2py
chown -R www-data:www-data /home/www-data/shebanq
sleep 2
service apache2 start
