#!/bin/bash

# Script to provision a machine that hosts SHEBANQ.
# Run it on your local computer.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: $(basename $0) scenario [Options] backup

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
    --user:   only backed-up user data

Backup:
    yyyy-mm-dd: take user data backed up at this date
"

setscenario "$1" "Provisioning" "$USAGE"
shift

doall="v"
doscripts="x"
docorpus="x"
doemdros="x"
doweb2py="x"
douser="x"

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
elif [[ "$1" == "--user" ]]; then
    doall="x"
    douser="v"
    shift
fi

backupdate="$1"
if [[ "$DBHOST" == "" ]]; then
    if [[ "$backupdate" == "" ]]; then
        if [[ "$doall" == "v" || "$douser" == "v" ]]; then
            echo "No backup date specified to retrieve user data from"
            exit
        fi
    elif [[ "$backupdate" != "" ]]; then
        shift
        backupsrcdir="$BACKUPDIR/$backupdate"
        if [[ ! -d "$backupsrcdir" ]]; then
            echo "Directory with user data backup does not exist: $backupsrcdir"
            exit
        fi
        if [[ "$doall" == "v" || "$douser" == "v" ]]; then
            uweb="$backupsrcdir/shebanq_web.sql.gz"
            unote="$backupsrcdir/shebanq_note.sql.gz"
            if [[ -f "$uweb" ]]; then
                scp -r "$uweb" "dirkr@$MACHINE:$TARGET"
            else
                echo "WARNING: shebanq_web data not found ($uweb)"
            fi
            if [[ -f "$unote" ]]; then
                scp -r "$unote" "dirkr@$MACHINE:$TARGET"
            else
                echo "WARNING: shebanq_note data not found ($unote)"
            fi
        else
            echo "user data backup exists but will not be uploaded"
        fi
    fi
else
    if [[ "$backupdate" != "" ]]; then
        echo "You passed backup data $backupdate."
        echo "However, no backups are needed for this machine."
        exit
    fi
fi

if [[ "$doall" == "v" || "$doscripts" == "v" ]]; then
    scp -r "$SCRIPTSOURCE/grants.sql" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/shebanq.cnf" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/parameters_443.py" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/routes.py" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/wsgi.conf" "dirkr@$MACHINE:$TARGET"

    scp -r "$SCRIPTSOURCE/.bash_profile" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$SCRIPTSOURCE/backup.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$SCRIPTSOURCE/catchup.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$SCRIPTSOURCE/install.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$SCRIPTSOURCE/update.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$SCRIPTSOURCE/updateData.sh" "dirkr@$MACHINE:$TARGETHOME"

    if [[ -e "$DESTCFG" ]]; then
        rm -rf "$DESTCFG"
    fi
    if [[ -e "$DESTAPA" ]]; then
        rm -rf "$DESTAPA"
    fi
    cp -r "$SOURCECFG" "$DESTCFG"
    cp -r "$SOURCEAPA" "$DESTAPA"
    scp -r "$SOURCECFG" "dirkr@$MACHINE:/$TARGET/"
    scp -r "$SOURCEAPA" "dirkr@$MACHINE:/$TARGET/"
fi

if [[ "$DBHOST" == "" ]]; then
    if [[ "$doall" == "v" || "$docorpus" == "v" ]]; then
        for version in $DATA_VERSIONS
        do
            echo "Uploading version $version ..."
            thissrc="$DATASOURCE/$version"
            scp -r "$thissrc/shebanq_etcbc$version.mql.bz2" "dirkr@$MACHINE:/$TARGET"
            scp -r "$thissrc/shebanq_passage$version.sql.gz" "dirkr@$MACHINE:/$TARGET"
        done

    fi
fi

if [[ "$doall" == "v" || "$doemdros" == "v" ]]; then
        echo "Uploading emdros binary version $EMDROSVERSION ..."
        scp -r "$EMDROS" "dirkr@$MACHINE:/$TARGET"
fi

if [[ "$doall" == "v" || "$doweb2py" == "v" ]]; then
        echo "Uploading web2py zip ..."
        scp -r "$WEB2PY" "dirkr@$MACHINE:/$TARGET"
fi
