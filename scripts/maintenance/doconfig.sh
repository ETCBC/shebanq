#!/bin/bash

org="etcbc"
APP="shebanq"
REPO="shebanq"
REPO_URL="https://github.com/$org/$REPO"

# All the following settings are by convention

sourceOrg="$githubBase/$org"
sourceRepo="$sourceOrg/$REPO"
SCRIPT_SRC_DIR="$sourceRepo/scripts"
LOCAL_DIR="$sourceRepo/_local"
packageDir="$SCRIPT_SRC_DIR/packages"

SERVER_HOME_DIR="/home/$SERVER_USER"
SERVER_INSTALL_DIR="$SERVER_HOME_DIR/$APP-install"
SERVER_BACKUP_DIR="$SERVER_HOME_DIR/$APP-backups"
SERVER_UNPACK_DIR="$SERVER_HOME_DIR/$APP-tmp"

SERVER_APP_DIR="/opt/web-apps"
SERVER_CFG_DIR="/opt/cfg"
SERVER_OLD_CFG_DIR="/opt/emdros/cfg"
SERVER_EMDROS_DIR="/opt/emdros"
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

TM="/usr/bin/time -f ElapsedTime=%E"
