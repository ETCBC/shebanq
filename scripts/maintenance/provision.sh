#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to provision a server.
# Run it on your local computer.

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) situation [Options] [version]

Provisions a $APP server with data to install it with.
It will look on your local server for the latest backup of the $APP server,
which contains the dynamic part of the database.

situation:
    pn: provision the new production server
    p:  provision the current production server
    t:  provision the test server
    o:  provision the current other server
    on:  provision the new other server

Options:
    --scripts: all the scripts and config data
    --static:  only static data (passage and etcbc databases)
    --dynamic: only dynamic data ($DYNAMIC_WEB and $DYNAMIC_NOTE)
    --emdros:  only Emdros binary
    --web2py:  only Web2py binary

version:
    a valid SHEBANQ data version, such as 4, 4b, c, 2017, 2021
    It will restrict the data provisioning to the databases
    that belong to this version.
    If left out, all versions will be done.
    Especially relevant if --static is passed.
"

showUsage "$1" "$USAGE"

setSituation "$1" "Provisioning" "$USAGE"
shift

doAll="v"
doScripts="x"
doStatic="x"
doDynamic="x"
doEmdros="x"
doWeb2py="x"

if [[ "$1" == "--scripts" ]]; then
    doAll="x"
    doScripts="v"
    shift
elif [[ "$1" == "--static" ]]; then
    doAll="x"
    doStatic="v"
    shift
elif [[ "$1" == "--dynamic" ]]; then
    doAll="x"
    doDynamic="v"
    shift
elif [[ "$1" == "--emdros" ]]; then
    doAll="x"
    doEmdros="v"
    shift
elif [[ "$1" == "--web2py" ]]; then
    doAll="x"
    doWeb2py="v"
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

ssh "$SERVER_USER@$SERVER" "mkdir -p $SERVER_INSTALL_DIR"

latestBackup="$BACKUP_DIR/latest"

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doDynamic" == "v" ]]; then
        echo "o-o-o previous dynamic data if any o-o-o"

        stampFile="$latestBackup/stamp"

        if [[ -f "$stampFile" ]]; then
            stamp=`cat "$stampFile"`
            echo "found backup made on $stamp"
        fi
        for db in $DYNAMIC_WEB $DYNAMIC_NOTE
        do
            dbFile="$latestBackup/${db}.sql.gz"
            if [[ ! -f "$dbFile" ]]; then
                echo "WARNING: no latest backup found for ($dbFile), we use an empty db"
                dbFile="$SCRIPT_SRC_DIR/${db}.sql.gz"
            fi
            scp -r "$dbFile" "$SERVER_USER@$SERVER:$SERVER_INSTALL_DIR"
        done
    fi
fi

if [[ "$doAll" == "v" || "$doScripts" == "v" ]]; then
    echo "o-o-o scripts o-o-o"

    for script in grants.sql routes.py shebanq.cnf parameters_443.py unconfigure.sql wsgi.conf
    do
        scp -r "$SCRIPT_SRC_DIR/$script" "$SERVER_USER@$SERVER:$SERVER_INSTALL_DIR"
    done
    for script in backup.sh config.sh install.sh restore.sh uninstall.sh update.sh
    do
        scp -r "$LOCAL_SCRIPT_DIR/$script" "$SERVER_USER@$SERVER:$SERVER_HOME_DIR"
    done

    if [[ -e "$LOCAL_CFG" ]]; then
        rm -rf "$LOCAL_CFG"
    fi
    if [[ -e "$LOCAL_APA" ]]; then
        rm -rf "$LOCAL_APA"
    fi
    cp -r "$LOCAL_CFG_SPECIFIC" "$LOCAL_CFG"
    cp -r "$LOCAL_APA_SPECIFIC" "$LOCAL_APA"
    for item in "$LOCAL_CFG" "$LOCAL_APA"
    do
        scp -r "$item" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR/"
    done
fi

if [[ "$DB_HOST" == "" ]]; then
    if [[ "$doAll" == "v" || "$doStatic" == "v" ]]; then
        echo "o-o-o static data o-o-o"
        for version in $versions
        do
            echo "    o-o version $version ..."
            src="$STATIC_SRC_DIR/$version"
            staticEtcbc="${src}/${STATIC_ETCBC}$version.mql.bz2"
            staticPassage="${src}/${STATIC_PASSAGE}$version.sql.gz"
            for item in "$staticEtcbc" "$staticPassage"
            do
                scp -r "$item" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR"
            done
        done

    fi
fi

if [[ "$doAll" == "v" || "$doEmdros" == "v" ]]; then
        echo "o-o-o emdros package o-o-o"
        scp -r "$EMDROS_PATH" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR"
fi

if [[ "$doAll" == "v" || "$doWeb2py" == "v" ]]; then
        echo "o-o-o web2py package o-o-o"
        scp -r "$WEB2PY_PATH" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR"
fi
