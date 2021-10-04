#!/bin/bash

# give help if the user asks for it

function showUsage {
    if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "-?" ]]; then
        echo "$2"
        exit
    fi
}

# Set some variables that depend on the situation

function setSituation {
    if [[ "$1" == "p" || "$1" == "$serverProd" ]]; then
        SERVER="$serverProd"
        SERVER_URL="$serverUrlProd"
        DB_HOST="$dbHostProd"
        MYSQL_SHEBANQ="$mysqlShebanqPwdProd"
        MYSQL_SHEBANQ_ADMIN="$mysqlShebanqAdminPwdProd"
        CERT_FILE="$certFileProd"
        CERT_KEY="$certKeyProd"
        CERT_CHAIN="$certChainProd"
        echo "$2 PRODUCTION server $SERVER ..."
    elif [[ "$1" == "pn" || "$1" == "$serverProdNew" ]]; then
        SERVER="$serverProdNew"
        SERVER_URL="$serverUrlProd"
        DB_HOST="$dbHostProd"
        MYSQL_SHEBANQ="$mysqlShebanqPwdProd"
        MYSQL_SHEBANQ_ADMIN="$mysqlShebanqAdminPwdProd"
        CERT_FILE="$certFileProd"
        CERT_KEY="$certKeyProd"
        CERT_CHAIN="$certChainProd"
        echo "$2 PRODUCTION server (new) $SERVER ..."
    elif [[ "$1" == "t" || "$1" == "$serverTest" ]]; then
        SERVER="$serverTest"
        SERVER_URL="$serverUrlTest"
        DB_HOST="$dbHostTest"
        MYSQL_SHEBANQ="$mysqlShebanqPwdTest"
        MYSQL_SHEBANQ_ADMIN="$mysqlShebanqAdminPwdTest"
        CERT_FILE="$certFileTest"
        CERT_KEY="$certKeyTest"
        CERT_CHAIN="$certChainTest"
        echo "$2 TEST server $SERVER ..."
    elif [[ "$1" == "o" || "$1" == "$serverOther" ]]; then
        SERVER="$serverOther"
        SERVER_URL="$serverUrlOther"
        DB_HOST="$dbHostOther"
        MYSQL_SHEBANQ="$mysqlShebanqPwdOther"
        MYSQL_SHEBANQ_ADMIN="$mysqlShebanqAdminPwdOther"
        CERT_FILE="$certFileOther"
        CERT_KEY="$certKeyOther"
        CERT_CHAIN="$certChainOther"
        echo "$2 OTHER server $SERVER ..."
    elif [[ "$1" == "on" || "$1" == "$serverOtherNew" ]]; then
        SERVER="$serverOtherNew"
        SERVER_URL="$serverUrlOther"
        DB_HOST="$dbHostOther"
        MYSQL_SHEBANQ="$mysqlShebanqPwdOther"
        MYSQL_SHEBANQ_ADMIN="$mysqlShebanqAdminPwdOther"
        CERT_FILE="$certFileOther"
        CERT_KEY="$certKeyOther"
        CERT_CHAIN="$certChainOther"
        echo "$2 OTHER server (new) $SERVER ..."
    else
        echo "$3"
        exit
    fi
    KEYVALUES="
    SERVER=$SERVER
    SERVER_URL=$SERVER_URL
    DB_HOST=$DB_HOST
    MYSQL_SHEBANQ=$MYSQL_SHEBANQ
    MYSQL_SHEBANQ_ADMIN=$MYSQL_SHEBANQ_ADMIN
    CERT_FILE=$CERT_FILE
    CERT_KEY=$CERT_KEY
    CERT_CHAIN=$CERT_CHAIN
    "
}

# make sure a directory exists

function ensureDir {
    if [[ -f "$1" ]]; then
        rm -rf "$1"
    fi
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
    fi
}

# erase a directory if it exists

function eraseDir {
    if [[ -d "$1" ]]; then
        rm -rf "$1"
    fi
}

# compile the python code in a web2py application

function compileApp {
    app="$1"

    echo "- Compile $app ..."
    cmd1="import gluon.compileapp;"
    cmd2="gluon.compileapp.compile_application('applications/$app')"

    cd "$SERVER_APP_DIR/web2py"
    python3 -c "$cmd1 $cmd2" > /dev/null

    echo "- Compile modules of $app ..."
    cd "$SERVER_APP_DIR/web2py/applications/$app"
    python3 -m compileall modules > /dev/null
    echo "- Done compiling $app."
}

# clone or pull shebanq into the installation directory
# i.e. ~/shebanq-install/shebanq

function fetchShebanq {
    if [[ -d "$SERVER_INSTALL_DIR/$APP" ]]; then
        echo "o-o-o    SHEBANQ pull    o-o-o"
        cd "$SERVER_INSTALL_DIR/$APP"
        git fetch origin
        git checkout master
        git reset --hard origin/master
    else
        echo "o-o-o    SHEBANQ clone    o-o-o"
    cd "$SERVER_INSTALL_DIR"
        if [[ -e "$APP" ]]; then
            rm -rf "$APP"
        fi
        $TM git clone "$REPO_URL"
    fi
}

# put shebanq into place
# i.e. copy it from the install location to the web-apps location

function installShebanq {
    echo "o-o-o    INSTALL SHEBANQ    o-o-o"
    ensureDir "$SERVER_APP_DIR"
    chmod 755 /opt
    chmod 755 "$SERVER_APP_DIR"
    cd "$SERVER_APP_DIR"

    if [[ -e "$SERVER_APP_DIR/$APP" ]]; then
        rm -rf "$SERVER_APP_DIR/$APP"
    fi

    # copy the SHEBANQ repo from the install dir to the webapps dir
    # we do not copy the hidden files, such as the big .git directory
    mkdir "$SERVER_APP_DIR/$APP"
    cp -R $SERVER_INSTALL_DIR/$APP/* "$SERVER_APP_DIR/$APP"

    # warming up
    cd "$SERVER_APP_DIR"
    chown -R apache:apache $APP
    if [[ -e "$SERVER_APP_DIR/web2py" ]]; then
        compileApp $APP
        chown -R apache:apache "$SERVER_APP_DIR/$APP"
        chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/$APP"
    fi
}

# run a controller of shebanq outside the apache ocntext

function testController {
    echo "o-o-o    TEST CONTROLLER o-o-o"

    cd "$SERVER_APP_DIR/web2py"
    $TM python3 web2py.py -S $APP/hebrew/text -M > /dev/null
    chown -R apache:apache "$SERVER_APP_DIR/$APP"
    chcon -R -t httpd_sys_content_t "$SERVER_APP_DIR/$APP"
}

# make a first visit to SHEBANQ by means of curl

function firstVisit {
    echo "o-o-o    FIRST VISIT (this might take a minute)   o-o-o"
    echo "o-o-o An expensive index will be computed and cached"

    fullUrl="https://$SERVER_URL/$TEST_CONTROLLER"
    echo "fetching $fullUrl"
    $TM curl "https://$SERVER_URL/$TEST_CONTROLLER" | tail
}
