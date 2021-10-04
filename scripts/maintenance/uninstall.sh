#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to install a server.
# Run it on the server.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options] [version]

Without options, it runs the complete un-installation process for a $APP server.
By means of options, you can select exactly one step to be performed.

NOTE:
This script will not remove the provisions directory ~/shebanq-install
or anything in it. That means that the install action fetchShebanq is not undone.

Options:
    --python: the python programming language
    --emdros: the emdros software
    --mysqlinstall: install mariadb (drop-in replacement of mysql)
    --mysqlconfig: configure mysql
    --static: load static data into mysql
    --dynamic: load dynamic data into mysql
    --$APP: clone $REPO
    --web2py: install web2py
    --apache: setup apache (assume certificates are already in place)

version:
    a valid SHEBANQ data version, such as 4, 4b, c, 2017, 2021
    It will restrict the data provisioning to the databases
    that belong to this version.
    If left out, all versions will be done.
    Especially relevant if --static is passed.

"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Installing" "$USAGE"

doAll="v"
doPython="x"
doEmdros="x"
doMysqlinstall="x"
doMysqlConfig="x"
doStatic="x"
doDynamic="x"
doShebanq="x"
doWeb2py="x"
doApache="x"

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
elif [[ "$1" == "--$APP" ]]; then
    doAll="x"
    doShebanq="v"
    shift
elif [[ "$1" == "--web2py" ]]; then
    doAll="x"
    doWeb2py="v"
    shift
elif [[ "$1" == "--apache" ]]; then
    doAll="x"
    doApache="v"
    shift
fi

if [[ "$1" == "" ]]; then
    versions="$STATIC_VERSIONS"
else
    versions="$1"
    shift
fi

# generic stuff

eraseDir "$SERVER_UNPACK_DIR"

# Uninstall procedure

# uninstall web2py

if [[ "$doAll" == "v" || "$doWeb2py" == "v" ]]; then
    echo "o-o-o    WEB2PY REMOVAL    o-o-o"
    if [[ -e "$SERVER_APP_DIR/web2py" ]]; then
        rm -rf "$SERVER_APP_DIR/web2py"
    fi
    # remove /opt/web-apps if it is empty
    if ls -1qA "$SERVER_APP_DIR" | grep -q .
    then
        echo "not removing $SERVER_APP_DIR_YET"
    else
        rm -rf "$SERVER_APP_DIR"
    fi
fi

# uninstall Shebanq

if [[ "$doAll" == "v" || "$doShebanq" == "v" ]]; then
    echo "o-o-o    SHEBANQ REMOVAL    o-o-o"
    if [[ -e "$SERVER_APP_DIR/$APP" ]]; then
        rm -rf "$SERVER_APP_DIR/$APP"
    fi
    # remove /opt/web-apps if it is empty
    if ls -1qA "$SERVER_APP_DIR" | grep -q .
    then
        echo "not removing $SERVER_APP_DIR_YET"
    else
        rm -rf "$SERVER_APP_DIR"
    fi
fi

# Drop static data:
#   passage databases
#   emdros databases

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doStatic" == "v" ]]; then
        echo "o-o-o    DROP STATIC DATA   o-o-o"

        mysqlOpt="--defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt"

        for version in $versions
        do
            for db in "$STATIC_PASSAGE$version" "$STATIC_ETCBC$version"
            do
                mysql $mysqlOpt -e "drop database if exists $db;"
            done
        done
    fi
fi

# Drop dynamic data:
#   user-generated-content databases in the right order

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doDynamic" == "v" ]]; then
        echo "o-o-o    DROP DYNAMIC DATA  o-o-o"

        mysqlOpt="--defaults-extra-file=$SERVER_CFG_DIR/mysqldumpopt"

        for db in $DYNAMIC_NOTE $DYNAMIC_WEB
        do
            mysql $mysqlOpt -e "drop database if exists $db;"
        done
    fi
fi

# unconfigure mysql

if [[ "$doAll" == "v" || "$doMysqlConfig" == "v" ]]; then
    echo "o-o-o    UNCONFIGURE MYSQL    o-o-o"

    cd "$SERVER_INSTALL_DIR"
    mysql -u root < unconfigure.sql
fi


# uninstall emdros

if [[ "$doAll" == "v" || "$doEmdros" == "v" ]]; then
    echo "o-o-o    Emdros REMOVAL    o-o-o"

    if [[ -e "$SERVER_EMDROS_DIR" ]]; then
        rm -rf "$SERVER_EMDROS_DIR"
    fi
fi

# uninstall MariaDB

if [[ "$doAll" == "v" || "$doMysqlinstall" == "v" ]]; then
    echo "o-o-o    UNINSTALL MARIADB    o-o-o"
    service mariadb stop
    yum -q -y remove mariadb-server.x86_64
    yum -q -y remove mariadb-devel.x86_64
    yum -q -y remove mariadb.x86_64
fi

# Python

if [[ "$doAll" == "v" || "$doPython" == "v" ]]; then
    echo "o-o-o    UNINSTALL PYTHON o-o-o"
    yum -q -y remove mod_wsgi
    yum -q -y remove python3-markdown
    yum -q -y remove python36-devel
    yum -q -y remove python36
fi
