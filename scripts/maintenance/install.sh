#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to install a server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options] [version]

Without options, it runs the complete installation process for a $APP server.
By means of options, you can select exactly one step to be performed.
The server must have been provisioned.

Options:
    --python: the python programming language
    --emdros: the emdros software
    --mysqlinstall: install mariadb (drop-in replacement of mysql)
    --mysqlconfig: configure mysql
    --static: load static data into mysql
    --dynamic: load dynamic data into mysql
    --fetch$APP: clone or pull $REPO
    --$APP: install $REPO
    --web2py: install web2py
    --testcontroller: run a controller in the web2py shell for testing
    --apache: setup apache (assume certificates are already in place)
    --firstvisit: run controller from shell, outside apache, to warm up cache

version:
    a valid SHEBANQ data version, such as 4, 4b, c, 2017, 2021
    It will restrict the data provisioning to the databases
    that belong to this version.
    If left out, all versions will be done.
    Especially relevant if --static is passed.

CAUTION
Take care with installing the current production server.
It might damage the current installation.
"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Installing" "$USAGE"

ensureDir "$SERVER_UNPACK_DIR"

doAll="v"
doPython="x"
doEmdros="x"
doMysqlinstall="x"
doMysqlConfig="x"
doStatic="x"
doDynamic="x"
doFetchShebanq="x"
doShebanq="x"
doWeb2py="x"
doTestController="x"
doApache="x"
doFirstVisit="x"

if [[ "$1" == "--python" ]]; then
    doAll="x"
    doPython="v"
    shift
elif [[ "$1" == "--emdros" ]]; then
    doAll="x"
    doEmdros="v"
    shift
elif [[ "$1" == "--mysqlinstall" ]]; then
    doAll="x"
    doMysqlinstall="v"
    shift
elif [[ "$1" == "--mysqlconfig" ]]; then
    doAll="x"
    doMysqlConfig="v"
    shift
elif [[ "$1" == "--static" ]]; then
    doAll="x"
    doStatic="v"
    shift
elif [[ "$1" == "--dynamic" ]]; then
    doAll="x"
    doDynamic="v"
    shift
elif [[ "$1" == "--fetch$APP" ]]; then
    doAll="x"
    doFetchShebanq="v"
    shift
elif [[ "$1" == "--$APP" ]]; then
    doAll="x"
    doShebanq="v"
    shift
elif [[ "$1" == "--web2py" ]]; then
    doAll="x"
    doWeb2py="v"
    shift
elif [[ "$1" == "--testcontroller" ]]; then
    doAll="x"
    doTestController="v"
    shift
elif [[ "$1" == "--apache" ]]; then
    doAll="x"
    doApache="v"
    shift
elif [[ "$1" == "--firstvisit" ]]; then
    doAll="x"
    doFirstVisit="v"
    shift
elif [[ "$1" == --* ]]; then
    echo "Unrecognized switch: $1"
    echo "Do ./$(basename $0) --help for available options"
    exit
fi

if [[ "$1" == "" ]]; then
    versions="$STATIC_VERSIONS"
else
    versions="$1"
    shift
fi

# stuff to get the emdros stuff working

# needed for the mql command
PATH=$PATH:$HOME/.local/bin:$HOME/bin
EMDROS_HOME=/opt/emdros
export EMDROS_HOME
PATH=$EMDROS_HOME/bin:$PATH
export PATH

# Install procedure

# Python

if [[ "$doAll" == "v" || "$doPython" == "v" ]]; then
    echo "o-o-o    INSTALL PYTHON o-o-o"
    $TM yum -q -y install python36
    $TM yum -q -y install python36-devel
    $TM yum -q -y install python3-markdown
    # we need the python command (for emdros compilation)
    alternatives --set python /usr/bin/python3
    $TM yum -q -y install mod_wsgi
fi

# MariaDB
# * install mariadb

if [[ "$doAll" == "v" || "$doMysqlinstall" == "v" ]]; then
    echo "o-o-o    INSTALL MARIADB    o-o-o"
    $TM yum -q -y install mariadb.x86_64
    $TM yum -q -y install mariadb-devel.x86_64
    $TM yum -q -y install mariadb-server.x86_64

    service mariadb start
fi


# Configure mysql databases, set users and grants

skipUsers="x"
skipGrants="x"

if [[ "$doAll" == "v" || "$doMysqlConfig" == "v" ]]; then
    echo "o-o-o    CONFIGURE MYSQL    o-o-o"

    cd "$SERVER_INSTALL_DIR"

    if [[ "$DB_HOST" == "" ]]; then
        cp shebanq.cnf /etc/my.cnf.d/
        if [[ "$skipUsers" != "v" ]]; then
            echo "o-o-o - create users"
            mysql -u root < "$SERVER_CFG_DIR/user.sql"
        fi
        if [[ "$skipGrants" != "v" ]]; then
            echo "o-o-o - grant privileges"
            mysql -u root < grants.sql
        fi
    fi

    setsebool -P httpd_can_network_connect 1
    setsebool -P httpd_can_network_connect_db 1
fi

# Emdros

if [[ "$doAll" == "v" || "$doEmdros" == "v" ]]; then
    echo "o-o-o    INSTALL Emdros    o-o-o"

    cd "$SERVER_INSTALL_DIR"
    tar xvf "$EMDROS_FILE" > /dev/null
    cd "$EMDROS_BARE"

    echo "o-o-o - Emdros CONFIGURE"
    $TM ./configure --prefix=$SERVER_EMDROS_DIR --with-sqlite3=no --with-mysql=yes --with-swig-language-java=no --with-swig-language-python2=no --with-swig-language-python3=yes --with-postgresql=no --with-wx=no --with-swig-language-csharp=no --with-swig-language-php7=no --with-bpt=no --disable-debug > /dev/null

    echo "o-o-o - Emdros MAKE (may take 5-10 minutes)"
    echo "There will be some alarming warnings, but that's ok"
    $TM make > /dev/null

    echo "o-o-o - Emdros INSTALL"
    echo "There will be some warnings, but that's ok"
    $TM make install > /dev/null

    cp -r "$SERVER_INSTALL_DIR/cfg" "$SERVER_EMDROS_DIR"
    chown -R apache:apache "$SERVER_EMDROS_DIR"
fi

# Import dynamic data:
#   user-generated-content databases, previously save in a backup

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doDynamic" == "v" ]]; then
        echo "o-o-o    LOAD DYNAMIC DATA start    o-o-o"
        for db in $DYNAMIC_WEB $DYNAMIC_NOTE
        do
            echo "o-o-o - DB $db"

            echo "o-o-o - creating fresh $db"
            mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e "drop database if exists $db;"
            mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt -e "create database $db;"

            echo "o-o-o - unzipping $db"
            cp "$SERVER_INSTALL_DIR/$db.sql.gz" "$SERVER_UNPACK_DIR"
            $TM gunzip -f "$SERVER_UNPACK_DIR/$db.sql.gz"

            echo "o-o-o - loading $db"
            $TM echo "use $db" | cat - $SERVER_UNPACK_DIR/$db.sql | mysql --defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt

            rm "$SERVER_UNPACK_DIR/$db.sql"
        done
        echo "o-o-o    LOAD DYNAMIC DATA end    o-o-o"
    fi
fi

# Import static data:
#   passage databases
#   emdros databases

skipPdb="x"
skipEdb="x"

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doStatic" == "v" ]]; then
        echo "o-o-o    LOAD STATIC DATA start    o-o-o"

        mysqlOpt="--defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt"

        for version in $versions
        do
            if [[ "$skipPdb" != "v" ]]; then
                echo "o-o-o - VERSION $version ${STATIC_PASSAGE}"
                db="$STATIC_PASSAGE$version"
                echo "o-o-o - unzipping $db"
                cp "$SERVER_INSTALL_DIR/$db.sql.gz" "$SERVER_UNPACK_DIR"
                $TM gunzip -f "$SERVER_UNPACK_DIR/$db.sql.gz"
                echo "o-o-o - loading $db (may take half a minute)"
                $TM mysql $mysqlOpt < "$SERVER_UNPACK_DIR/$db.sql"
                rm "$SERVER_UNPACK_DIR/$db.sql"
            fi

            if [[ "$skipEdb" != "v" ]]; then
                echo "o-o-o - VERSION $version ${STATIC_ETCBC}"
                db="$STATIC_ETCBC$version"
                echo "o-o-o - unzipping $db"
                cp $SERVER_INSTALL_DIR/$db.mql.bz2 $SERVER_UNPACK_DIR
                $TM bunzip2 -f $SERVER_UNPACK_DIR/$db.mql.bz2
                echo "o-o-o - dropping $db"
                mysql $mysqlOpt -e "drop database if exists $db;"
                echo "o-o-o - importing $db (may take a minute or two)"
                mqlPwd=`cat $SERVER_CFG_DIR/mqlimportopt`
                mqlOpt="-e UTF8 -n -b m -u $MYSQL_ADMIN"
                $TM $SERVER_MQL_DIR/mql $mqlOpt -p $mqlPwd < $SERVER_UNPACK_DIR/$db.mql
                rm "$SERVER_UNPACK_DIR/$db.mql"
            fi
        done
        echo "o-o-o    LOAD STATIC DATA end    o-o-o"
    fi
fi

# fetch Shebanq

if [[ "$doAll" == "v" || "$doFetchShebanq" == "v" ]]; then

    if [[ -d "$SERVER_INSTALL_DIR/$APP" ]]; then
        echo "o-o-o    SHEBANQ pull    o-o-o"
        cd "$SERVER_INSTALL_DIR/$APP"
        git fetch origin
        git checkout master
        git reset --hard origin/master
    else
        echo "o-o-o    SHEBANQ clone    o-o-o"
    cd "$SERVER_INSTALL_DIR"
        if [[ -e "$APP" ]]; then
            rm -rf "$APP"
        fi
        $TM git clone "$REPO_URL"
    fi
fi

# install Shebanq

if [[ "$doAll" == "v" || "$doShebanq" == "v" ]]; then
    echo "o-o-o    INSTALL SHEBANQ    o-o-o"
    ensureDir "$SERVER_APP_DIR"
    chmod 755 /opt
    chmod 755 "$SERVER_APP_DIR"
    cd "$SERVER_APP_DIR"

    if [[ -e "$SERVER_APP_DIR/$APP" ]]; then
        rm -rf "$SERVER_APP_DIR/$APP"
    fi

    # copy the SHEBANQ repo from the install dir to the webapps dir
    # we do not copy the hidden files, such as the big .git directory
    mkdir "$SERVER_APP_DIR/$APP"
    cp -R $SERVER_INSTALL_DIR/$APP/* "$SERVER_APP_DIR/$APP"

    # warming up
    cd "$SERVER_APP_DIR"
    chown -R apache:apache $APP
    if [[ -e "$SERVER_APP_DIR/web2py" ]]; then
        compileApp $APP
        chown -R apache:apache "$SERVER_APP_DIR/$APP"
        chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/$APP"
    fi
fi

# install web2py

skipExtradirs="x"

if [[ "$doAll" == "v" || "$doWeb2py" == "v" ]]; then
    echo "o-o-o    WEB2PY START    o-o-o"

    # unpack Web2py

    echo "o-o-o - install"
    ensureDir "$SERVER_APP_DIR"
    chmod 755 /opt
    chmod 755 "$SERVER_APP_DIR"

    cd "$SERVER_APP_DIR"
    cp "$SERVER_INSTALL_DIR/$WEB2PY_FILE" web2py.zip
    if [[ -e web2py ]]; then
        rm -rf web2py
    fi
    $TM unzip web2py.zip > /dev/null
    rm web2py.zip
    mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py

    for pyFile in parameters_443.py routes.py
    do
        cp "$SERVER_INSTALL_DIR/$pyFile" web2py
    done

    compileApp admin

    echo "o-o-o - Removing examples app"
    rm -rf "$SERVER_APP_DIR/web2py/applications/examples"

    setsebool -P httpd_tmp_exec on

    # hook up SHEBANQ

    echo "o-o-o - hookup $APP"
    cd "$SERVER_APP_DIR/web2py/applications"
    if [[ -e $APP ]]; then
        rm -rf $APP
    fi
    ln -s "$SERVER_APP_DIR/$APP" "$APP"
    chown apache:apache "$APP"

    if [[ -e "$APP" ]]; then
        compileApp $APP
        chown -R apache:apache "$SERVER_APP_DIR/$APP"
        chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/$APP"
    fi

    cd "$SERVER_APP_DIR"
    chown -R apache:apache web2py
    chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/web2py"

    if [[ "$skipExtradirs" != "v" ]]; then
        echo "o-o-o - make writable dirs"
        cd "$SERVER_APP_DIR/web2py/applications"
        for app in welcome admin $APP
        do
            for dir in languages databases cache errors sessions private uploads
            do
                # if [[ -e ${app}/${dir} ]]; then
                #     rm -rf ${app}/${dir}
                # fi
                if [[ ! -e ${app}/${dir} ]]; then
                    mkdir ${app}/${dir}
                fi
                chown -R apache:apache ${app}/${dir}
                # chcon -R -t tmp_t ${app}/${dir}
                chcon -R -t httpd_sys_rw_content_t ${app}/${dir}
            done
        done
    fi

fi

# test controller to spot errors

if [[ "$doAll" == "v" || "$doTestController" == "v" ]]; then
    echo "o-o-o    TEST CONTROLLER o-o-o"

    cd "$SERVER_APP_DIR/web2py"
    $TM python3 web2py.py -S $APP/hebrew/text -M > /dev/null
    chown -R apache:apache "$SERVER_APP_DIR/$APP"
    chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/$APP"
fi

# configure apache

if [[ "$doAll" == "v" || "$doApache" == "v" ]]; then
    echo "o-o-o    APACHE setup    o-o-o"

    if [[ -e "$APACHE_DIR/welcome.conf" ]]; then
        mv "$APACHE_DIR/welcome.conf" "$APACHE_DIR/welcome.conf.disabled"
    fi
    cp $SERVER_INSTALL_DIR/apache/*.conf "$APACHE_DIR"
    cp "$SERVER_INSTALL_DIR/wsgi.conf" "$APACHE_DIR"

    service httpd restart
fi

eraseDir "$SERVER_UNPACK_DIR"

# first Visit to warm-up caches and to verify that the setup works

if [[ "$doAll" == "v" || "$doFirstVisit" == "v" ]]; then
    echo "o-o-o    FIRST VISIT    o-o-o"

    $TM curl "$SERVER_URL/$TEST_CONTROLLER" | tail
fi

# Todo after install
#
# Let DNS resolve the server name to the IP address of the newly
# installed server
