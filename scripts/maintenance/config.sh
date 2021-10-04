#!/bin/bash

# BEFORE YOU START !!
#
# before running any maintenance script:
#
# - read maintenance.md
# - tweak the parameters in the next section
# - read and understand the script that you want to run

# ALL_CAPS variables are used by the other scripts
# camelCase variables only occur in this file

org="etcbc"
APP="shebanq"
REPO="shebanq"
REPO_URL="https://github.com/$org/$REPO"

# TWEAKING PART #################################################
#
# !!!!!!!!
# CAUTION: make sure you have copied the maintenance directory
# to the _local directory of your $REPO clone.
# This directory will not be pushed online.
#
# Do not tweak the original files in the scripts/maintenance directory
# !!!!!!!!
#
# Adapt the following settings to your situation before
# running the maintenance scripts.
#
#
# Version of the Emdros software that is in use.
# see also https://emdros.org
#
emdrosVersion="3.7.3"
#
#
# Version of the Web2Py software that is in use.
# see also https://github.com/web2py/web2py
#
web2pyVersion="2.21.1-stable"
#
#
#
# Versions of the ETCBC data that you want to install/update
# NB: the $APP software has hardcoded references to these versions.
#
STATIC_VERSIONS="4 4b 2017 c 2021"
#
#
# Where backups of the user-generated data of $APP can be found
# When installing the  $APP on a new server with a
# new database, you should make a backup of this data and put
# it here, under a diretory named yyyy-mm-dd
# The provision script will copy that over to the server and
# import it in the new database.
# There is a separate setting for backups made
# on the test server, the new production server, and the new other server.
#
BACKUP_DIR=~/local/$APP/backups
BACKUP_ALT_DIR=~/local/$APP/backupsAlt
#
#
# Where your local github directory resided, under which 
# the $REPO has been cloned.
# N.B. The clone of $REPO is then $githubBase/$org/$REPO
#
githubBase=~/github
#
#
# Your username on the server
#
SERVER_USER="dirkr"
#
#
# Where the Apache config files are on the server
APACHE_DIR="/etc/httpd/conf.d"
#
#
# Server specifications
# The specification of the server in the different situations
# If you work with the official SHEBANQ, the PROD and TEST servers
# are relevant.
# If you are bravely setting up SHEBANQ somewhere else,
# use the OTHER server settings.
#
# serverXxx is the server name as internet address
# 
# For each Xxx in Other, OtherNew, Test, Prod, ProdNew we define:
#
# serverUrlXxx: the url of shebanq when served from this server;
#
# dbHostXxx is the host server where the mysql database resides
#   Leave it empty if there is a local mysql server
#   If mysql is served on an other server, we
#   assume that the data is still in place when we install SHEBANQ
#   So we do not create database users, administer database grants,
#   and fill database tables.
#   We also assumes that the grants of the database server
#   are not host specific, so that when we access the database from a
#   new server, the same grants apply as when we used the old server
#   
serverProd="clarin11.dans.knaw.nl"
serverProdNew="clarin31.dans.knaw.nl"
serverUrlProd="https://shebanq.ancient-data.org"
dbHostProd="-h mysql11.dans.knaw.nl"

serverTest="tclarin31.dans.knaw.nl"
serverUrlTest="https://test.shebanq.ancient-data.org"
dbHostTest=""

serverOther="other1.server.edu"
serverOtherNew="other2.server.edu"
serverUrlOther="https://shebanq.mydomain.org"
dbHostOther=""
#
# END TWEAKING PART #################################################


# All the following settings are by convention

sourceOrg="$githubBase/$org"
sourceRepo="$sourceOrg/$REPO"
SCRIPT_SRC_DIR="$sourceRepo/scripts"
localDir="$sourceRepo/_local"
LOCAL_SCRIPT_DIR="$localDir/maintenance"
packageDir="$SCRIPT_SRC_DIR/packages"

SERVER_HOME_DIR="/home/$SERVER_USER"
SERVER_INSTALL_DIR="$SERVER_HOME_DIR/$APP-install"
SERVER_BACKUP_DIR="$SERVER_HOME_DIR/$APP-backups"
SERVER_UNPACK_DIR="$SERVER_HOME_DIR/$APP-tmp"

SERVER_APP_DIR="/opt/web-apps"
SERVER_EMDROS_DIR="/opt/emdros"
SERVER_CFG_DIR="$SERVER_EMDROS_DIR/cfg"
SERVER_MQL_DIR="$SERVER_EMDROS_DIR/bin"

STATIC_SRC_DIR="$sourceOrg/bhsa/$APP"
STATIC_ETCBC="shebanq_etcbc"
STATIC_PASSAGE="shebanq_passage"

DYNAMIC_WEB="shebanq_web"
DYNAMIC_NOTE="shebanq_note"

MYSQL_USER="shebanq"
MYSQL_ADMIN="shebanq_admin"

WEB2PY_BARE="web2py_src-$web2pyVersion"
WEB2PY_FILE="$WEB2PY_BARE.zip"
WEB2PY_PATH="$packageDir/$WEB2PY_FILE"

EMDROS_BARE="emdros-$emdrosVersion"
EMDROS_FILE="$EMDROS_BARE.tar.gz"
EMDROS_PATH="$packageDir/$EMDROS_FILE"

TEST_CONTROLLER="hebrew/text"

TM="time -f '%E' "

# Set some variables that depend on the situation

function showUsage {
    if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "-?" ]]; then
        echo "$2"
        exit
    fi
}

function setSituation {
    if [[ "$1" == "p" || "$1" == "$serverProd" ]]; then
        SERVER="$serverProd"
        SERVER_URL="$serverUrlProd"
        DB_HOST="$dbHostProd"
        LOCAL_CFG_SPECIFIC="$localDir/cfg_prod"
        LOCAL_APA_SPECIFIC="$localDir/apache_prod"
        echo "$2 PRODUCTION server $SERVER ..."
    elif [[ "$1" == "pn" || "$1" == "$serverProdNew" ]]; then
        SERVER="$serverProdNew"
        SERVER_URL="$serverUrlProd"
        DB_HOST="$dbHostProd"
        LOCAL_CFG_SPECIFIC="$localDir/cfg_prod"
        LOCAL_APA_SPECIFIC="$localDir/apache_prod"
        echo "$2 PRODUCTION server (new) $SERVER ..."
    elif [[ "$1" == "t" || "$1" == "$serverTest" ]]; then
        SERVER="$serverTest"
        SERVER_URL="$serverUrlTest"
        DB_HOST="$dbHostTest"
        LOCAL_CFG_SPECIFIC="$localDir/cfg_test"
        LOCAL_APA_SPECIFIC="$localDir/apache_test"
        echo "$2 TEST server $SERVER ..."
    elif [[ "$1" == "o" || "$1" == "$serverOther" ]]; then
        SERVER="$serverOther"
        SERVER_URL="$serverUrlOther"
        DB_HOST="$dbHostOther"
        LOCAL_CFG_SPECIFIC="$localDir/cfg_other"
        LOCAL_APA_SPECIFIC="$localDir/apache_other"
        echo "$2 OTHER server $SERVER ..."
    elif [[ "$1" == "on" || "$1" == "$serverOtherNew" ]]; then
        SERVER="$serverOtherNew"
        SERVER_URL="$serverUrlOther"
        DB_HOST="$dbHostOther"
        LOCAL_CFG_SPECIFIC="$localDir/cfg_other"
        LOCAL_APA_SPECIFIC="$localDir/apache_other"
        echo "$2 OTHER server (new) $SERVER ..."
    else
        echo "$3"
        exit
    fi

    LOCAL_CFG="$sourceRepo/_local/cfg"
    LOCAL_APA="$sourceRepo/_local/apache"
}

function ensureDir {
    if [[ -f "$1" ]]; then
        rm -rf "$1"
    fi
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
    fi
}

function eraseDir {
    if [[ -d "$1" ]]; then
        rm -rf "$1"
    fi
}

function compileApp {
    app="$1"

    echo "- Compile $app ..."
    cmd1="import gluon.compileapp;"
    cmd2="gluon.compileapp.compile_application('applications/$app')"

    cd "$SERVER_APP_DIR/web2py"
    python3 -c "$cmd1 $cmd2"

    echo "- Compile modules of $app ..."
    cd "$SERVER_APP_DIR/web2py/applications/$app"
    python3 -m compileall modules
    echo "- Done compiling $app."
}
