#!/bin/bash

# ABOUT
#
# This is the configuration of the maintenance scripts of SHEBANQ
# on a server that hosts it. It is not meant for local installations.
# By the way, SHEBANQ can be installed on a personal computer,
# but that is not explained here.
#
# The maintenance scripts are
#
# * backup.sh
#   - Run on the server.
#   - Stop the web service
#   - Backup the databases that have dynamic web data
#       shebanq_web
#       shebanq_note
#   - Start the services
#
# * save.sh
#   - Run on your local machine.
#   - Save backups of dynamic web data from the shebanq server to your
#     local directory where you hold backups.
#     in a subfolder yyyy-mm-dd (the date of the backup).
#     See BACKUPDIR below.
#
# * provision.sh
#   - Run on your local machine.
#   - Copy all files needed for installation from your local
#     machine to the shebanq server.
#   - These files end up in shebanq-install under your home directory
#   - Also the maintenance scripts files will be copied over
#     to your home directory on the server.
#
# * install.sh
#   - Run on the server.
#     Install and configure required software:
#       MySQL, Python, Emdros, Web2py, shebanq itself
#   - Fill the databases with data.
#   - Start the services.
#
# * restore.sh
#   - Run on the server.
#   - Stop the web service
#   - Backup the databases that have dynamic web data
#   - Start the services
#
# * update.sh
#   - Run on the server.
#   - Stop the services
#   - Pull shebanq
#   - Start the services
#

# CONVENTIONS
#
# There are three scenarios, depending on the machine that hosts SHEBANQ:
#
# Production:   shebanq.ancient-data.org
#                   the one and only offical shebanq website
#                   publicly accessible
#                   hosted by DANS on a KNAW server
# Test:         test.shebanq.ancient-data.orgs
#                   the one and only offical shebanq test website
#                   accessible from within the DANS-KNAW network
#                   hosted by DANS on a KNAW server
# Other:        url to be configured
#                   an unoffical shebanq website (we encourage that!)
#                   access to be configured
#                   hosting to be configured
#
# REQUIREMENTS
#
# * You have cloned shebanq to your local computer,
#   prefarably to ~/github/etcbc/shebanq
#   You may change the ~/github location below, but you must keep
#   the organization and repo directory structure.
#
# * You need to create a directory _local in ~/github/etcbc/shebanq
#   with subdirectories
#
#   `cfg_prod`, `apache_prod` and/or
#   `cfg_test`, `apache_test` and/or
#   `cfg_other`, `apache_tother`
#
#   depending on the scenario.
#   The contents of these directories should mimick
#   the public directories
#   `cfg_other` and `cfg_apache`
#   found under scripts in the cloned shebanq repository.
# 
# * You install SHEBANQ on a Security Enhanced Linux Server (SELINUX);
#   - you can access this machine by means of ssh (and scp)
#   - you can sudo on this machine
#
# * Apache is already installed, /etc/httpd exists
#   - mod_wsgi is not yet installed
#   - the relevant certificates are installed in
#     /etc/pki/tls/certs and /etc/pki/tls/private
#     and correctly referred to in the apache conf file
#     in your _local/apache_xxx directory, where
#     xxx is prod/test/other depending on the scenario
#
# AFTER INSTALL
#
# Make sure that DNS resolves the server address to the IP address of
# the newly installed machine.


# TWEAKING PART #################################################
#
# Adapt the following settings to your situation before
# running the maintenance scripts.
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
# Where your local github directory resided, under which 
# the shebanq repo has been cloned.
# N.B. The clone of shebanq is then $SOURCEGH/etcbc/shebanq
SOURCEGH=~/github
#
#
# Machine specifications
# The specification of the machines in the different scenarios
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
MACHINE_PROD="clarin31.dans.knaw.nl"
DBHOST_PROD="-h mysql11.dans.knaw.nl"

MACHINE_TEST="tclarin31.dans.knaw.nl"
DBHOST_TEST=""

MACHINE_OTHER="other.machine.edu"
LOCALDB_OTHER="v"
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
# END TWEAKING PART #################################################


# All the following settings are by convention

SOURCEORG="$SOURCEGH/etcbc"
SOURCEREPO="$SOURCEORG/shebanq"
DATASOURCE="$SOURCEORG/bhsa/shebanq"
SCRIPTSOURCE="$SOURCEREPO/scripts"
LOCALDIR="$SOURCEREPO/_local"
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

# Set some variables that depend on the scenario

function showusage {
    if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "-?" ]]; then
        echo "$2"
        exit
    fi
}

function setscenario {
    if [[ "$1" == "p" || "$1" == "$MACHINE_PROD" ]]; then
        MACHINE="$MACHINE_PROD"
        DBHOST="$DBHOST_PROD"
        SOURCECFG="$LOCALDIR/cfg_prod"
        SOURCEAPA="$LOCALDIR/apache_prod"
        echo "$2 PRODUCTION machine $MACHINE ..."
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
