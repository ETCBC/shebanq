#!/bin/bash

# Script to provision a shebanq server.
# Run it on your local computer.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) scenario [Options]

Provisions a shebanq server with data to install it with.
It will look on your local machine for the latest backup of the shebanq server,
which contains the dynamic part of the database.

N.B.: After provisioning the server, before running install.sh
on the server, make sure you do it in a fresh terminal.
Because provisioning updates the .bash_profile on the server.

scenario:
    p: provision the production machine
    t: provision the test machine
    o: provision the other machine

Options:
    --corpus: only ETCBC data
    --emdros: only Emdros binary
    --web2py: only Web2py binary
    --backup: only backup data
"

showusage "$1" "$USAGE"

setscenario "$1" "Provisioning" "$USAGE"
shift

doall="v"
doscripts="x"
docorpus="x"
doemdros="x"
doweb2py="x"
dobackup="x"

if [[ "$1" == "--scripts" ]]; then
    doall="x"
    doscripts="v"
    shift
elif [[ "$1" == "--corpus" ]]; then
    doall="x"
    docorpus="v"
    shift
elif [[ "$1" == "--emdros" ]]; then
    doall="x"
    doemdros="v"
    shift
elif [[ "$1" == "--web2py" ]]; then
    doall="x"
    doweb2py="v"
    shift
elif [[ "$1" == "--backup" ]]; then
    doall="x"
    dobackup="v"
    shift
fi

LATESTBACKUP="$BACKUPDIR/latest"

if [[ "$DBHOST" == "" ]]; then
    if [[ "$doall" == "v" || "$dobackup" == "v" ]]; then
        if [[ ! -d "$LATESTBACKUP" ]]; then
            echo "No latest server backup found"
            exit
        fi
        uweb="$LATESTBACKUP/shebanq_web.sql.gz"
        unote="$LATESTBACKUP/shebanq_note.sql.gz"
        for db in shebanq_web shebanq_note
        do
            dbfile="$LATESTBACKUP/${db}.sql.gz"
            if [[ -f "$dbfile" ]]; then
                scp -r "$dbfile" "$TARGETUSER@$MACHINE:$TARGET"
            else
                echo "WARNING: $db data not found ($dbfile)"
            fi
        done
    fi
fi

if [[ "$doall" == "v" || "$doscripts" == "v" ]]; then
    for script in grants.sql shebanq.cnf parameters_443.py routes.py wsgi.conf
    do
        scp -r "$SCRIPTSOURCE/$script" "$TARGETUSER@$MACHINE:$TARGET"
    done
    for script in .bash_profile backup.sh restore.sh config.sh install.sh update.sh
    do
        scp -r "$SCRIPTSOURCE/$script" "$TARGETUSER@$MACHINE:$TARGETHOME"
    done

    if [[ -e "$DESTCFG" ]]; then
        rm -rf "$DESTCFG"
    fi
    if [[ -e "$DESTAPA" ]]; then
        rm -rf "$DESTAPA"
    fi
    cp -r "$SOURCECFG" "$DESTCFG"
    cp -r "$SOURCEAPA" "$DESTAPA"
    scp -r "$SOURCECFG" "$TARGETUSER@$MACHINE:/$TARGET/"
    scp -r "$SOURCEAPA" "$TARGETUSER@$MACHINE:/$TARGET/"
fi

if [[ "$DBHOST" == "" ]]; then
    if [[ "$doall" == "v" || "$docorpus" == "v" ]]; then
        for version in $DATA_VERSIONS
        do
            echo "Uploading version $version ..."
            thissrc="$DATASOURCE/$version"
            scp -r "$thissrc/shebanq_etcbc$version.mql.bz2" "$TARGETUSER@$MACHINE:/$TARGET"
            scp -r "$thissrc/shebanq_passage$version.sql.gz" "$TARGETUSER@$MACHINE:/$TARGET"
        done

    fi
fi

if [[ "$doall" == "v" || "$doemdros" == "v" ]]; then
        echo "Uploading emdros binary version $EMDROSVERSION ..."
        scp -r "$EMDROS" "$TARGETUSER@$MACHINE:/$TARGET"
fi

if [[ "$doall" == "v" || "$doweb2py" == "v" ]]; then
        echo "Uploading web2py zip ..."
        scp -r "$WEB2PY" "$TARGETUSER@$MACHINE:/$TARGET"
fi
