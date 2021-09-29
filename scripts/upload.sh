EMDROSVERSION="3.7.3"
DATA_VERSIONS="4 4b 2017 c 2021"

SOURCEGH=~/github
SOURCEORG="$SOURCEGH/etcbc"
SOURCEREPO="$SOURCEORG/shebanq"
DATASOURCE="$SOURCEORG/bhsa/shebanq"
SCRIPTSOURCE="$SOURCEREPO/scripts"
HOMESOURCE="$SCRIPTSOURCE/home"
LOCALDIR="$SOURCEREPO/_local"
BINARIES="$SCRIPTSOURCE/binaries"
EMDROS="$BINARIES/emdros-$EMDROSVERSION.tar.gz"
WEB2PY="$BINARIES/web2py_src.zip"
BACKUPDIR=~/Documents/Current/SHEBANQ/maintenance/backupShebanqUserData

# change the next value to your home directory on the destination machine
#
TARGETHOME='/home/dirkr'
TARGET="$TARGETHOME/shebanq-install"


if [[ "$1" == "p" ]]; then
    PRODUCTION="v"
    MACHINE="clarin31.dans.knaw.nl"
    LOCALDB="x"
    SOURCECFG="$SOURCEREPO/_local/cfg_prod"
    SOURCEAPA="$SOURCEREPO/_local/apache_prod"
    echo "Uploading to PRODUCTION machine $MACHINE ..."
elif [[ "$1" == "t" ]]; then
    echo "Uploading to TEST machine $MACHINE ..."
    PRODUCTION="x"
    MACHINE="tclarin31.dans.knaw.nl"
    LOCALDB="v"
    SOURCECFG="$SOURCEREPO/_local/cfg_test"
    SOURCEAPA="$SOURCEREPO/_local/apache_test"
elif [[ "$1" == "o" ]]; then
    echo "Uploading to OTHER machine $MACHINE ..."
    PRODUCTION="x"
    MACHINE="other.machine.edu"
    LOCALDB="v"
    SOURCECFG="$SOURCEREPO/scripts/cfg_other"
    SOURCEAPA="$SOURCEREPO/scripts/apache_other"
else
    echo "USAGE: ./upload.sh [pto] [--corpus] [--emdros] [--web2py] [--user] [yyyy-mm-dd]"
    echo "where p = production"
    echo "and   t = test"
    echo "and   o = other"
    echo "--corpus: only corpus data"
    echo "--emdros: only emdros binary"
    echo "--web2py: only web2py zip"
    echo "--user: only user data"
    echo "yyyy-mm-dd: take user data backed up at this date"
    exit
fi

DESTCFG="$SOURCEREPO/_local/cfg"
DESTAPA="$SOURCEREPO/_local/apache"

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
if [[ "$LOCALDB" == "v" ]]; then
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
    scp -r "$SCRIPTSOURCE/install.sh" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/grants.sql" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/shebanq.cnf" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/parameters_443.py" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/routes.py" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/wsgi.conf" "dirkr@$MACHINE:$TARGET"
    scp -r "$SCRIPTSOURCE/install.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$HOMESOURCE/.bash_profile" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$HOMESOURCE/backup.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$HOMESOURCE/catchup.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$HOMESOURCE/update.sh" "dirkr@$MACHINE:$TARGETHOME"
    scp -r "$HOMESOURCE/updateData.sh" "dirkr@$MACHINE:$TARGETHOME"

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

if [[ "$LOCALDB" == "v" ]]; then
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
