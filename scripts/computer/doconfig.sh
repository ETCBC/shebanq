#!/bin/bash

ORG="etcbc"
APP="shebanq"
REPO="shebanq"
REPO_URL="https://github.com/$ORG/$REPO"

# All the following settings are by convention

sourceOrg="$githubBase/$ORg"
sourceRepo="$sourceOrg/$REPO"
SCRIPT_SRC_DIR="$sourceRepo/scripts"
packageDir="$SCRIPT_SRC_DIR/packages"

SERVER_APP_DIR=~/Applications/SHEBANQ
SERVER_EMDROS_DIR="/opt/emdros"

STATIC_SRC_DIR="$sourceOrg/bhsa/$APP"
STATIC_ETCBC="shebanq_etcbc"
STATIC_PASSAGE="shebanq_passage"

DYNAMIC_WEB="shebanq_web"
DYNAMIC_NOTE="shebanq_note"

MYSQL_USER="shebanq"

WEB2PY_BARE="web2py_src-$web2pyVersion"
WEB2PY_FILE="$WEB2PY_BARE.zip"
WEB2PY_PATH="$packageDir/$WEB2PY_FILE"

EMDROS_BARE="emdros-$emdrosVersion"
EMDROS_FILE="$EMDROS_BARE.tar.gz"
EMDROS_PATH="$packageDir/$EMDROS_FILE"
