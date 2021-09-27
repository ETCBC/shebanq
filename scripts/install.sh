#!/bin/bash

# 2021-09-07 Dirk Roorda

# script by which shebanq is installed on fresh staging and production selinux servers.
# It is assumed that the data used by the production machine resides
# in a database on a separate database server.
# We assume the grants in the production machine are wildcarded
# in the sense that
# * they are not host specific,
#   so users with the right names on mew machines have the same access
# * they are not data version specific,
#   so when new data versions arrive, their corresponding
#   databases are accessible by the right users

# So, when we install a new production server, we do not:
# * make new mysql users
# * grant/revoke access to databases/tables
# * load data
#
# But all these steps will be done on the test server.

# Use update.sh to update data on production and test servers.

# run it as follows:
#
# ./install.sh [options]
#
# By means of the options you can select one single step to execute.
# See below.

# This script is set up to work at specific servers.
# Currently it supports one production machine and one staging machine, both SELINUX.

# CFG_DIR   : directory with config files for talking with mysql
# MQL_DIR   : directory with the mql command
# APP_DIR   : directory where the web app shebanq resides (and also web2py itself)
# INCOMING  : directory where installation files arrive
# UNPACK    : directory where installation files are unpacked

MACHINE_PROD="clarin31.dans.knaw.nl"
MACHINE_TEST="tclarin31.dans.knaw.nl"

TOPLEVEL="/home/dirkr"
INCOMING="/home/dirkr/shebanq-install"
UNPACK="$INCOMING/unpack"

APP_DIR="/opt/web-apps"
WEB2PY_DIR="$APP_DIR/web2py"
SHEBANQ_DIR="$APP_DIR/shebanq"
EMDROS_DIR="/opt/emdros"
CFG_DIR="$EMDROS_DIR/cfg"
MQL_DIR="$EMDROS_DIR/bin"

APACHE_DIR="/etc/httpd/conf.d"

EMDROSVERSION="3.7.3"
WEB2PY="web2py_src.zip"

DATA_VERSIONS="4 4b 2017 c 2021"

if [ -f "$UNPACK" ]; then
    rm -rf "$UNPACK"
fi
if [ ! -d "$UNPACK" ]; then
    mkdir -p "$UNPACK"
fi

if [ "$HOSTNAME" == "$MACHINE_PROD" ]; then
    echo "Installing PRODUCTION machine ..."
    PRODUCTION="v"
elif [ "$HOSTNAME" == "$MACHINE_TEST" ]; then
    echo "Installing STAGING machine ..."
    PRODUCTION="x"
else
    echo "Install not supported on machine $HOSTNAME"
    exit
fi

doall="v"
dopython="x"
doemdros="x"
domysqlinstall="x"
domysqlconfig="x"
domysqlload="x"
doshebanq="x"
doweb2py="x"
doapache="x"

if [ "$1" == "--dopython" ]; then
    doall="x"
    dopython="v"
    shift
elif [ "$1" == "--emdros" ]; then
    doall="x"
    doemdros="v"
    shift
elif [ "$1" == "--mysqlinstall" ]; then
    doall="x"
    domysqlinstall="v"
    shift
elif [ "$1" == "--mysqlconfig" ]; then
    doall="x"
    domysqlconfig="v"
    shift
elif [ "$1" == "--mysqlload" ]; then
    doall="x"
    domysqlload="v"
    shift
elif [ "$1" == "--shebanq" ]; then
    doall="x"
    doshebanq="v"
    shift
elif [ "$1" == "--web2py" ]; then
    doall="x"
    doweb2py="v"
    shift
elif [ "$1" == "--apache" ]; then
    doall="x"
    doapache="v"
    shift
else
    echo "USAGE: ./install.sh [--python] [--emdros]"
    echo "--python: only python modules"
    echo "--emdros: only emdros building"
    echo "--mysqlinstall: only mysql installation"
    echo "--mysqlconfig: only mysql configuration"
    echo "--mysqlload: only mysql data loading"
    echo "--shebanq: clone shebanq"
    echo "--web2py: install web2py"
    echo "--apache: setup apache"
    exit
fi

# Situation before install

# Apache
# /etc/httpd exists (there is no mod_wsgi module installed)
# no relevant certificates in /etc/pki/tls/certs
# (need ancient-data_org_cert.cer and possibly ancient-data_org_interm.cer)
#
# Python
# * python3 command works, installed version is 3.8.6
# * python module markdown not yet installed
# * command mysql does not work

# Todo before install
# * run ./upload.sh in order to get all installation material on to the target machine
# NB: one of these files is `.bash_profile`.
# When you log in on the target machine, and after that do the upload,
# make sure to do source .bash_profile or log out and log on.

# * Make sure the grants on the PRODUCTION machine give access to the shebanq users

# Install procedure

# Python
# * install module markdown (probably sudo pip3 install markdown)

if [ "$doall" == "v" ] || [ "$dopython" == "v" ]; then
    echo "0-0-0    INSTALL PYTHON MODULES    0-0-0"
    yum install python36-devel
    yum install python3-markdown
fi

# MariaDB
# * (test only) install mariadb
# * configure mariadb
# * (/etc/my.cnf should contain default-character-set=utf8)
# * create users shebanq and shebanq_admin
# * grant rights on tables to these users

if [ "$doall" == "v" ] || [ "$domysqlinstall" == "v" ]; then
    echo "0-0-0    INSTALL MARIADB    0-0-0"
    yum install mariadb.x86_64
    yum install mariadb-devel.x86_64
    yum install mariadb-server.x86_64

    service mariadb start
fi

if [ "$doall" == "v" ] || [ "$doemdros" == "v" ]; then
    echo "0-0-0    INSTALL EMDROS    0-0-0"
    cd "$INCOMING"
    tar xvf "emdros-$EMDROSVERSION.tar.gz"
    cd "emdros-$EMDROSVERSION"

    echo "EMDROS CONFIGURE"
    ./configure --prefix=$EMDROS_DIR --with-sqlite3=no --with-mysql=yes --with-swig-language-java=no --with-swig-language-python2=no --with-swig-language-python3=yes --with-postgresql=no --with-wx=no --with-swig-language-csharp=no --with-swig-language-php7=no --with-bpt=no --disable-debug

    echo "EMDROS MAKE"
    make

    echo "EMDROS INSTALL"
    make install

    cp -r "$INCOMING/cfg" "$EMDROS_DIR"
    chown -R apache:apache "$EMDROS_DIR"
fi

skipusers="v"
skipgrants="v"

if [ "$doall" == "v" ] || [ "$domysqlconfig" == "v" ]; then
    echo "0-0-0    CONFIGURE MYSQL    0-0-0"

    if [ "$PRODUCTION" == "x" ]; then
        cp shebanq.cnf /etc/my.cnf.d/
        if [ "$skipusers" != "v" ]; then
            echo "0-0-0        create users        0-0-0"
            mysql -u root < "$CFG_DIR/user.sql"
        fi
        if [ "$skipgrants" != "v" ]; then
            echo "0-0-0        grant privileges        0-0-0"
            mysql -u root < grants.sql
        fi
    fi

    setsebool -P httpd_can_network_connect 1
    setsebool -P httpd_can_network_connect_db 1
fi

skippdb="x"
skipedb="x"
skipudb="x"

if [ "$doall" == "v" ] || [ "$domysqlload" == "v" ]; then
    echo "0-0-0    LOAD DATA start    0-0-0"
    for version in $DATA_VERSIONS
    do
        if [ "$skippdb" != "v" ]; then
            echo "0-0-0        VERSION $version passage        0-0-0"
            pdbname="shebanq_passage$version"
            echo "unzipping $pdbname"
            cp "$INCOMING/$pdbname.sql.gz" "$UNPACK"
            gunzip -f "$UNPACK/$pdbname.sql.gz"
            echo "loading $pdbname"
            mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt < "$UNPACK/$pdbname.sql"
            rm "$UNPACK/$pdbname.sql"
        fi

        if [ "$skipedb" != "v" ]; then
            echo "0-0-0        VERSION $version emdros        0-0-0"
            edbname="shebanq_etcbc$version"
            echo "unzipping $edbname"
            cp $INCOMING/$edbname.mql.bz2 $UNPACK
            bunzip2 -f $UNPACK/$edbname.mql.bz2
            echo "dropping $edbname"
            mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "drop database if exists $edbname;"
            echo "importing $edbname"
            $MQL_DIR/mql -n -b m -p `cat $CFG_DIR/mqlimportopt` -u shebanq_admin -e UTF8 < $UNPACK/$edbname.mql
            rm "$UNPACK/$edbname.mql"
        fi
    done
    if [ "$skipudb" != "v" ]; then
        for udbname in shebanq_note shebanq_web
        do
            echo "0-0-0        DB $udbname        0-0-0"

            echo "creating fresh $udbname"
            mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "drop database if exists $udbname;"
            mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "create database $udbname;"

            echo "unzipping $udbname"
            cp "$INCOMING/$udbname.sql.gz" "$UNPACK"
            gunzip -f "$UNPACK/$udbname.sql.gz"

            echo "loading $udbname"
            echo "use $udbname" | cat - $UNPACK/$udbname.sql | mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt

            rm "$UNPACK/$udbname.sql"
        done
    fi
    echo "0-0-0    LOAD DATA end    0-0-0"
fi

skipclone="v"

if [ "$doall" == "v" ] || [ "$doshebanq" == "v" ]; then
    cd "$APP_DIR"
    if [ "$skipclone" == "v" ]; then
        echo "0-0-0    SHEBANQ pull    0-0-0"
        cd shebanq
        git reset --hard
        git pull origin master
        cd "$APP_DIR"
        chown -R apache:apache shebanq
        cd web2py
        python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
    else
        echo "0-0-0    SHEBANQ clone    0-0-0"
        git clone "https://github.com/etcbc/shebanq"
    fi
    cp $SHEBANQ_DIR/scripts/home/*.sh $TOPLEVEL
fi

skipwsgi="x"
skipweb2py="x"
skipshebanq="x"
skipextradirs="x"

if [ "$doall" == "v" ] || [ "$doweb2py" == "v" ]; then
    echo "0-0-0    WEB2PY start    0-0-0"
    current_dir=`pwd`

    if [ -d /tmp/setup-web2py/ ]; then
        mv /tmp/setup-web2py/ /tmp/setup-web2py.old/
    fi

    mkdir -p /tmp/setup-web2py
    cd /tmp/setup-web2py

    if [ "$skipwsgi" != "v" ]; then
        echo "0-0-0        INSTALL mod_wsgi        0-0-0"
        yum install mod_wsgi
    fi

    if [ "$skipweb2py" != "v" ]; then
        echo "0-0-0        INSTALL web2py        0-0-0"
        if [ ! -d "$APP_DIR" ]; then
            mkdir -p "$APP_DIR"
            chmod 755 /opt
            chmod 755 "$APP_DIR"
        fi

        cd "$APP_DIR"
        cp "$INCOMING/$WEB2PY" .
        unzip $WEB2PY
        rm $WEB2PY
        mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
        cp "$INCOMING/parameters_443.py" web2py
        cp "$INCOMING/routes.py" web2py

        cd "$WEB2PY_DIR"
        echo "Compiling python code in admin"
        python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/admin')"

        echo "Removing welcome app"
        rm -rf "$WEB2PY_DIR/applications/welcome"
        rm -rf "$WEB2PY_DIR/applications/examples"
        rm -rf "$WEB2PY_DIR/welcome.w2p"

        setsebool -P httpd_tmp_exec on
    fi

    if [ "$skipshebanq" != "v" ]; then
        echo "0-0-0        HOOKUP shebanq        0-0-0"
        cd "$WEB2PY_DIR/applications"
        if [ -e shebanq ]; then
            rm -rf shebanq
        fi
        ln -s "$APP_DIR/shebanq" shebanq

        cd "$APP_DIR"
        chown -R apache:apache web2py
        chown -R apache:apache shebanq

        echo "Compiling python code in shebanq"
        cd web2py
        python -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
    fi

    if [ "$skipextradirs" != "v" ]; then
        echo "0-0-0        MAKE writable dirs        0-0-0"
        cd "$WEB2PY_DIR/applications"
        for app in `ls`
        do
            if [ "$app" == "__init__.py" ] || [ "$app" == "__pycache__" ]; then
                continue
            fi
            for dir in databases cache errors sessions private uploads
            do
                if [ -e ${app}/${dir} ]; then
                    rm -rf ${app}/${dir}
                fi
                mkdir ${app}/${dir}
                chown apache:apache ${app}/${dir}
                chcon -R -t tmp_t ${app}/${dir}
            done
        done
    fi
fi

if [ "$doall" == "v" ] || [ "$doapache" == "v" ]; then
    echo "0-0-0    APACHE setup    0-0-0"

    if [ -e "$APACHE_DIR/welcome.conf" ]; then
        mv "$APACHE_DIR/welcome.conf" "$APACHE_DIR/welcome.conf.disabled"
    fi
    cp $INCOMING/apache/*.conf "$APACHE_DIR"
    cp "$INCOMING/wsgi.conf" "$APACHE_DIR"

    service httpd restart
fi

exit

# Todo after install
#
# * shebanq.ancient-data.org should resolve to the production machine
