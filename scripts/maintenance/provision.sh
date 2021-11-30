#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to provision a server.
# Run it on your local computer.

if [[ ! -e "${0%/*}/config.sh" ]]; then
    echo "No config.sh found
Probably you are running this script from the maintenance directory.
You should run it from the _local directory where you have your
localized config.sh.

Hint: do

./localize.sh
cd ../../_local
    "
    exit
fi

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh


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

# transfer scripts from _local to server

ssh "$SERVER_USER@$SERVER" "mkdir -p $SERVER_INSTALL_DIR"

if [[ "$doAll" == "v" || "$doScripts" == "v" ]]; then
    echo "o-o-o scripts o-o-o"

    good="v"

    for script in grants.sql shebanq.cnf unconfigure.sql wsgi.conf
    do
        theFile="$SCRIPT_SRC_DIR/$script"
        if [[ -e "$theFile" ]]; then
            scp -r "$theFile" "$SERVER_USER@$SERVER:$SERVER_INSTALL_DIR"
        else
            good="x"
            echo "File not found: $theFile"
        fi
    done

    for script in backup.sh config.sh doconfig.sh functions.sh install.sh restore.sh uninstall.sh update.sh 'test.sh'
    do
        theFile="$LOCAL_DIR/$script"
        if [[ -e "$theFile" ]]; then
            scp -r "$theFile" "$SERVER_USER@$SERVER:$SERVER_HOME_DIR"
        else
            good="x"
            echo "File not found: $theFile"
        fi
    done

    for script in parameters_443.py
    do
        theFile="$LOCAL_DIR/$script"
        if [[ -e "$theFile" ]]; then
            scp -r "$theFile" "$SERVER_USER@$SERVER:$SERVER_INSTALL_DIR"
        else
            echo "Warning: administrative interface. No file $theFile provided."
            echo "In order to use the administrative interface you need this file.
            After installation you can generate it on the server and put it into your
            $LOCAL_DIR
            "
        fi
    done

    for template in apache.conf mail.cfg host.cfg mql.cfg mqlimportopt mysqldumpopt user.sql
    do
        theTemplate="$SCRIPT_SRC_DIR/maintenance/templates/$template"
        theFile="$LOCAL_DIR/$template"
        theFill="$SCRIPT_SRC_DIR/maintenance/fill.py"
        if [[ -e "$theTemplate" ]]; then
            python3 "$theFill" "$theTemplate" "$theFile" "$KEYVALUES" 
            if [[ "$template" == "apache.conf" ]]; then
                theConf="$LOCAL_DIR/${SERVER_URL}.conf"
                mv "$theFile" "$theConf"
                theFile="$theConf"
            fi
            scp -r "$theFile" "$SERVER_USER@$SERVER:$SERVER_INSTALL_DIR"
        else
            good="x"
            "Template not found: $theTemplate"
        fi
    done

    if [[ "$good" == "x" ]]; then
        exit
    fi
fi

# transfer dynamic data from latest backup stored locally to server

latestBackup="$BACKUP_DIR/latest"

if [[ "$DB_HOST" == "localhost" ]]; then
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

# transfer static data from local bhsa clones to server
# the only way to do this for new static data to a production server
# that does not store the data on itself, is by an explicit --static

if [[ "$doAll" == "v" || "$doStatic" == "v" ]]; then
    if [[ "$DB_HOST" == "localhost" || "$doAll" == "x" ]]; then
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

# transfer emdros zip from local shebanq clone to server

if [[ "$doAll" == "v" || "$doEmdros" == "v" ]]; then
        echo "o-o-o emdros package o-o-o"
        scp -r "$EMDROS_PATH" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR"
fi

# transfer web2py zip from local shebanq clone to server

if [[ "$doAll" == "v" || "$doWeb2py" == "v" ]]; then
        echo "o-o-o web2py package o-o-o"
        scp -r "$WEB2PY_PATH" "$SERVER_USER@$SERVER:/$SERVER_INSTALL_DIR"
fi
