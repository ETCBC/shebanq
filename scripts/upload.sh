INCOMING="/home/dirkr/shebanq-install"
DATA_VERSIONS="4 4b 2017 c 2021"
DATASOURCE="/Users/dirk/github/etcbc/bhsa/shebanq"
SCRIPTSOURCE="/Users/dirk/github/etcbc/shebanq/scripts"

BACKUPDIR="/Users/dirk/Documents/Current/SHEBANQ/maintenance/backupShebanqUserData"

LOCALDIR="/Users/dirk/github/etcbc/shebanq/_local"
EMDROSVERSION="3.7.3"
EMDROS="$LOCALDIR/emdros-$EMDROSVERSION.tar.gz"
WEB2PY="$LOCALDIR/web2py_src.zip"

TARGETHOME="/home/dirkr"
TARGET="$TARGETHOME/shebanq-install"


if [ "$1" == "p" ]; then
    echo "Uploading to PRODUCTION machine ..."
    PRODUCTION="v"
    MACHINE="clarin31.dans.knaw.nl"
elif [ "$1" == "t" ]; then
    echo "Uploading to STAGING machine ..."
    PRODUCTION="x"
    MACHINE="tclarin31.dans.knaw.nl"
else
    echo "USAGE: ./upload.sh [pt] [--corpus] [--emdros] [--web2py] [--user] [yyyy-mm-dd]"
    echo "where p = production"
    echo "and   t = test"
    echo "--corpus: only corpus data"
    echo "--emdros: only emdros binary"
    echo "--web2py: only web2py zip"
    echo "--user: only user data"
    echo "yyyy-mm-dd: take user data backed up at this date"
    exit
fi

shift
doall="v"
doscripts="x"
docorpus="x"
doemdros="x"
doweb2py="x"
douser="x"

if [ "$1" == "--scripts" ]; then
    doall="x"
    doscripts="v"
    shift
elif [ "$1" == "--corpus" ]; then
    doall="x"
    docorpus="v"
    shift
elif [ "$1" == "--emdros" ]; then
    doall="x"
    doemdros="v"
    shift
elif [ "$1" == "--web2py" ]; then
    doall="x"
    doweb2py="v"
    shift
elif [ "$1" == "--user" ]; then
    doall="x"
    douser="v"
    shift
fi

backupdate="$1"
if [ "$backupdate" == "" ]; then
    if [ "$doall" == "v" ] || [ "$douser" == "v" ]; then
        echo "No backup date specified to retrieve user data from"
        exit
    fi
elif [ "$backupdate" != "" ]; then
    shift
    backupsrcdir="$BACKUPDIR/$backupdate"
    if [ ! -d "$backupsrcdir" ]; then
        echo "Directory with user data backup does not exist: $backupsrcdir"
        exit
    fi
    if [ "$doall" == "v" ] || [ "$douser" == "v" ]; then
        uweb="$backupsrcdir/shebanq_web.sql.gz"
        unote="$backupsrcdir/shebanq_note.sql.gz"
        if [ -f "$uweb" ]; then
            scp -r "$uweb" "dirkr@$MACHINE:/$TARGET"
        else
            echo "WARNING: shebanq_web data not found ($uweb)"
        fi
        if [ -f "$unote" ]; then
            scp -r "$unote" "dirkr@$MACHINE:/$TARGET"
        else
            echo "WARNING: shebanq_note data not found ($unote)"
        fi
    else
        echo "user data backup exists but will not be uploaded"
    fi
fi

if [ "$doall" == "v" ] || [ "$doscripts" == "v" ]; then
    scp -r "$SCRIPTSOURCE/install.sh" "dirkr@$MACHINE:/$TARGET"
    scp -r "$SCRIPTSOURCE/.bash_profile" "dirkr@$MACHINE:/$TARGETHOME"
    scp -r "$SCRIPTSOURCE/grants.sql" "dirkr@$MACHINE:/$TARGET"
    scp -r "$SCRIPTSOURCE/shebanq.cnf" "dirkr@$MACHINE:/$TARGET"
    scp -r "$SCRIPTSOURCE/parameters_443.py" "dirkr@$MACHINE:/$TARGET"
    scp -r "$SCRIPTSOURCE/routes.py" "dirkr@$MACHINE:/$TARGET"
    scp -r "$SCRIPTSOURCE/wsgi.conf" "dirkr@$MACHINE:/$TARGET"

    if [ "$PRODUCTION" == "v" ]; then
        sourcecfg="cfg_prod"
        sourceapa="apache_prod"
    else
        sourcecfg="cfg_test"
        sourceapa="apache_test"
    fi
    if [ -e "$LOCALDIR/cfg" ]; then
        rm -rf "$LOCALDIR/cfg"
    fi
    if [ -e "$LOCALDIR/apache" ]; then
        rm -rf "$LOCALDIR/apache"
    fi
    cp -r "$LOCALDIR/$sourcecfg" "$LOCALDIR/cfg"
    cp -r "$LOCALDIR/$sourceapa" "$LOCALDIR/apache"
    scp -r "$LOCALDIR/cfg" "dirkr@$MACHINE:/$TARGET/"
    scp -r "$LOCALDIR/apache" "dirkr@$MACHINE:/$TARGET/"
fi

if [ "$doall" == "v" ] || [ "$docorpus" == "v" ]; then
    for version in $DATA_VERSIONS
    do
        echo "Uploading version $version ..."
        thissrc="$DATASOURCE/$version"
        scp -r "$thissrc/shebanq_etcbc$version.mql.bz2" "dirkr@$MACHINE:/$TARGET"
        scp -r "$thissrc/shebanq_passage$version.sql.gz" "dirkr@$MACHINE:/$TARGET"
    done

fi

if [ "$doall" == "v" ] || [ "$doemdros" == "v" ]; then
        echo "Uploading emdros binary version $EMDROSVERSION ..."
        scp -r "$EMDROS" "dirkr@$MACHINE:/$TARGET"
fi

if [ "$doall" == "v" ] || [ "$doweb2py" == "v" ]; then
        echo "Uploading web2py zip ..."
        scp -r "$WEB2PY" "dirkr@$MACHINE:/$TARGET"
fi
