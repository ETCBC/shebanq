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
Usage: ./$(basename $0)

Provisions the docker build context with data to install it with.
"

showUsage "$1" "$USAGE"

setSituation

# transfer data to build environment of the shebanq-db image

dest="$DOCKER_DIR/shebanq-db"
ensureDir "$dest"
for file in grants.sql shebanq.cnf
do
    cp "$SCRIPT_SRC_DIR/$file" "$dest"
done
for file in Dockerfile
do
    cp "$SCRIPT_SRC_DIR/docker/shebanq-db/$file" "$dest"
done

for template in mysqlrootopt user.sql
do
    theTemplate="$SCRIPT_SRC_DIR/docker/templates/$template"
    theFile="$DOCKER_DIR/shebanq-db/$template"
    theFill="$SCRIPT_SRC_DIR/docker/fill.py"
    if [[ -e "$theTemplate" ]]; then
        python3 "$theFill" "$theTemplate" "$theFile" "$KEYVALUES" 
    else
        good="x"
        "Template not found: $theTemplate"
    fi
done

# transfer data to build environment of the shebanq-db image

# - scripts, literally

dest="$DOCKER_DIR/shebanq"
ensureDir "$dest"
for file in Dockerfile unconfigure.sql wsgi.conf
do
    cp "$SCRIPT_SRC_DIR/docker/shebanq/$file" "$dest"
done
for file in routes.py wsgihandler.py
do
    cp "$SCRIPT_SRC_DIR/$file" "$dest"
done

# - scripts, as filled-in templates

for template in apache.conf mail.cfg host.cfg mql.cfg mqlimportopt mysqldumpopt user.sql \
    staticdata.sh
do
    theTemplate="$SCRIPT_SRC_DIR/docker/templates/$template"
    theFile="$DOCKER_DIR/shebanq/$template"
    theFill="$SCRIPT_SRC_DIR/docker/fill.py"
    if [[ -e "$theTemplate" ]]; then
        python3 "$theFill" "$theTemplate" "$theFile" "$KEYVALUES" 
        if [[ "$template" == "apache.conf" ]]; then
            theConf="$DOCKER_DIR/shebanq/${SERVER_URL}.conf"
            mv "$theFile" "$theConf"
        fi
    else
        good="x"
        "Template not found: $theTemplate"
    fi
done

# - dynamic data from latest backup

latestBackup="$BACKUP_DIR/latest"

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
    cp "$dbFile" "$DOCKER_DIR/shebanq"
done

# - static data from local bhsa clones

echo "o-o-o static data o-o-o"
for version in $STATIC_VERSIONS
do
    echo "    o-o version $version ..."
    src="$STATIC_SRC_DIR/$version"
    staticEtcbc="${src}/${STATIC_ETCBC}$version.mql.bz2"
    staticPassage="${src}/${STATIC_PASSAGE}$version.sql.gz"
    for item in "$staticEtcbc" "$staticPassage"
    do
        cp "$item" "$DOCKER_DIR/shebanq"
    done
done

# - emdros zip

echo "o-o-o emdros package o-o-o"
cp "$EMDROS_PATH" "$DOCKER_DIR/shebanq"

# - web2py zip

echo "o-o-o web2py package o-o-o"
cp "$WEB2PY_PATH" "$DOCKER_DIR/shebanq"
eraseDir "$DOCKER_DIR/shebanq/web2py"
unzip $WEB2PY_PATH -d "$DOCKER_DIR/shebanq" > /dev/null


for pyFile in routes.py wsgihandler.py
do
    sourceFile="$DOCKER_DIR/shebanq/$pyFile"
    destFile="$DOCKER_DIR/shebanq/web2py/$pyFile"
    cp "$sourceFile" "$destFile"
done

for pyFile in parameters_443.py
do
    sourceFile="$DOCKER_DIR/$pyFile"
    destFile="$DOCKER_DIR/shebanq/web2py/$pyFile"
    cp "$sourceFile" "$destFile"
done

# - shebanq webapp

echo "o-o-o shebanq app o-o-o"

eraseDir "$DOCKER_DIR/shebanq/shebanq"
ensureDir "$DOCKER_DIR/shebanq/shebanq"
for member in controllers cron models modules scripts static views
do
    cp -r "$SOURCE_REPO/$member" "$DOCKER_DIR/shebanq/shebanq/$member"
done
