#!/bin/bash

# BEFORE YOU START !!
#
# before running any maintenance script:
#
# - read maintenance.md
# - tweak the parameters in the next section
# - read and understand the script that you want to run


# TWEAKING PART #################################################
#
# !!!!!!!!
# CAUTION: make sure you have copied the maintenance directory
# to the _local directory of your shebanq clone.
# This directory will not be pushed online.
#
# Do not tweak the original files in the scripts/maintenance directory
# !!!!!!!!
#
# Adapt the following settings to your situation before
# running the maintenance scripts.
#
#
# Version of the EMDROS software that is in use.
# see also https://emdros.org
#
EMDROSVERSION="3.7.3"
#
#
# Versions of the ETCBC data that you want to install/update
# NB: the shebanq software has hardcoded references to these versions.
# If you only need to install/update a specific version
# tweak this parameter
#
DATA_VERSIONS="4 4b 2017 c 2021"
# DATA_VERSIONS="2021"
#
#
# Where backups of the user-generated data of shebanq can be found
# When installing the  shebanq on a new machine with a
# new database, you should make a backup of this data and put
# it here, under a diretory named yyyy-mm-dd
# The provision script will copy that over to the machine and
# import it in the new database
#
BACKUPDIR=~/local/shebanq/backups
#
#
# Where your local github directory resided, under which 
# the shebanq repo has been cloned.
# N.B. The clone of shebanq is then $SOURCEGH/etcbc/shebanq
#
SOURCEGH=~/github
#
#
# Your username on the server
#
TARGETUSER="dirkr"
#
#
# Where the Apache config files are on the server
APACHE_DIR="/etc/httpd/conf.d"
#
#
# Machine specifications
# The specification of the machines in the different situations
# If you work with the official SHEBANQ, the PROD and TEST machines
# are relevant.
# If you are bravely setting up SHEBANQ somewhere else,
# use the OTHER machine settings.
#
# MACHINE_xxx is the machine name as internet address
# DBHOST is the host machine where the mysql database resides
#   Leave it empty if there is a local mysql server
#   If mysql is served on an other server, we
#   assume that the data is still in place when we install SHEBANQ
#   So we do not create database users, administer database grants,
#   and fill database tables.
#   We also assumes that the grants of the database server
#   are not host specific, so that when we access the database from a
#   new machine, the same grants apply as when we used the old machine
#   
MACHINE_PROD="clarin11.dans.knaw.nl"
MACHINE_PROD_NEW="clarin31.dans.knaw.nl"
DBHOST_PROD="-h mysql11.dans.knaw.nl"

MACHINE_TEST="tclarin31.dans.knaw.nl"
DBHOST_TEST=""

MACHINE_OTHER="other.machine.edu"
MACHINE_OTHER_NEW="othernew.machine.edu"
DBHOST_OTHER="v"
#
# END TWEAKING PART #################################################


# All the following settings are by convention

SOURCEORG="$SOURCEGH/etcbc"
SOURCEREPO="$SOURCEORG/shebanq"
DATASOURCE="$SOURCEORG/bhsa/shebanq"
SCRIPTSOURCE="$SOURCEREPO/scripts"
LOCALDIR="$SOURCEREPO/_local"
MAINTENANCE="$LOCALDIR/maintenance"
BINARIES="$SCRIPTSOURCE/binaries"
EMDROS="$BINARIES/emdros-$EMDROSVERSION.tar.gz"
WEB2PY="$BINARIES/web2py_src.zip"

TARGETHOME="/home/$TARGETUSER"
TARGET="$TARGETHOME/shebanq-install"
TARGETBUDIR="$TARGETHOME/backups"
UNPACK="tmp/shebanq"

APP_DIR="/opt/web-apps"
WEB2PY_DIR="$APP_DIR/web2py"
SHEBANQ_DIR="$APP_DIR/shebanq"
EMDROS_DIR="/opt/emdros"
CFG_DIR="$EMDROS_DIR/cfg"
MQL_DIR="$EMDROS_DIR/bin"

EMDROSUNTAR="emdros-$EMDROSVERSION"
EMDROS="$EMDROS.tar.gz"
WEB2PY="web2py_src.zip"

# Set some variables that depend on the situation

function showusage {
    if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "-?" ]]; then
        echo "$2"
        exit
    fi
}

function setsituation {
    if [[ "$1" == "p" || "$1" == "$MACHINE_PROD" ]]; then
        MACHINE="$MACHINE_PROD"
        DBHOST="$DBHOST_PROD"
        SOURCECFG="$LOCALDIR/cfg_prod"
        SOURCEAPA="$LOCALDIR/apache_prod"
        echo "$2 PRODUCTION machine $MACHINE ..."
    elif [[ "$1" == "pn" || "$1" == "$MACHINE_PROD_NEW" ]]; then
        MACHINE="$MACHINE_PROD_NEW"
        DBHOST="$DBHOST_PROD"
        SOURCECFG="$LOCALDIR/cfg_prod"
        SOURCEAPA="$LOCALDIR/apache_prod"
        echo "$2 PRODUCTION machine (new) $MACHINE ..."
    elif [[ "$1" == "t" || "$1" == "$MACHINE_TEST" ]]; then
        MACHINE="$MACHINE_TEST"
        DBHOST="$DBHOST_TEST"
        SOURCECFG="$LOCALDIR/cfg_test"
        SOURCEAPA="$LOCALDIR/apache_test"
        echo "$2 TEST machine $MACHINE ..."
    elif [[ "$1" == "o" || "$1" == "$MACHINE_OTHER" ]]; then
        MACHINE="$MACHINE_OTHER"
        DBHOST="$DBHOST_OTHER"
        SOURCECFG="$LOCALDIR/cfg_other"
        SOURCEAPA="$LOCALDIR/apache_other"
        echo "$2 OTHER machine $MACHINE ..."
    elif [[ "$1" == "on" || "$1" == "$MACHINE_OTHER_NEW" ]]; then
        MACHINE="$MACHINE_OTHER_NEW"
        DBHOST="$DBHOST_OTHER"
        SOURCECFG="$LOCALDIR/cfg_other"
        SOURCEAPA="$LOCALDIR/apache_other"
        echo "$2 OTHER machine (new) $MACHINE ..."
    else
        echo "$3"
        exit
    fi

    DESTCFG="$SOURCEREPO/_local/cfg"
    DESTAPA="$SOURCEREPO/_local/apache"
}

function ensuredir {
    if [[ -f "$1" ]]; then
        rm -rf "$1"
    fi
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
    fi
}

function erasedir {
    if [[ -d "$1" ]]; then
        rm -rf "$1"
    fi
}
