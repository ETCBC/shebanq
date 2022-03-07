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
    KEYVALUES="
    SERVER=$SERVER
    SERVER_CFG_DIR=$SERVER_CFG_DIR
    SERVER_MQL_DIR=$SERVER_MQL_DIR
    SERVER_URL=$SERVER_URL
    STATIC_VERSIONS=$STATIC_VERSIONS
    STATIC_PASSAGE=$STATIC_PASSAGE
    STATIC_ETCBC=$STATIC_ETCBC
    DB_HOST=$DB_HOST
    MYSQL_ROOT=$MYSQL_ROOT
    MYSQL_SHEBANQ=$MYSQL_SHEBANQ
    MYSQL_SHEBANQ_ADMIN=$MYSQL_SHEBANQ_ADMIN
    CERT_FILE=$CERT_FILE
    CERT_KEY=$CERT_KEY
    CERT_CHAIN=$CERT_CHAIN
    MAIL_SERVER=$MAIL_SERVER
    MAIL_SENDER=$MAIL_SENDER
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
    fresh="$2"

    echo "o-o-o - compile $app"

    if [[ "$app" == "$APP" ]]; then
        parentDir="$SERVER_APP_DIR"
    else
        parentDir="$SERVER_APP_DIR/web2py/applications"
    fi

    appPath="$parentDir/$app"
    generatedDir="$appPath/compiled"
    if [[ ! -e "$generatedDir" ]]; then
        mkdir "$generatedDir"
        chmod -R 775 "$generatedDir" 
        chmod 2775 "$generatedDir" 
        setfacl -d -m g::rw "$generatedDir"
        chown "$SERVER_USER":shebanq "$generatedDir"
    fi
    cmd1="import gluon.compileapp;"
    cmd2="gluon.compileapp.compile_application('applications/$app')"

    cd "$SERVER_APP_DIR/web2py"
    python3 -c "$cmd1 $cmd2" > /dev/null

    if [[ "$fresh" == "v" ]]; then
        chown -R "$SERVER_USER":shebanq "$generatedDir"
    else
        chown -R --from=$SERVER_USER "$SERVER_USER":shebanq "$generatedDir"
    fi

    echo "- Compile modules of $app ..."
    cd "$SERVER_APP_DIR/web2py/applications/$app"
    python3 -m compileall modules > /dev/null

    generatedDir="$appPath/modules/__pycache__"
    if [[ ! -e "$generatedDir" ]]; then
        mkdir "$generatedDIr"
        chmod -R 775 "$generatedDir" 
        chmod 2775 "$generatedDir" 
        setfacl -d -m g::rw "$generatedDir"
        chown "$SERVER_USER":shebanq "$generatedDir"
    fi
    if [[ "$fresh" == "v" ]]; then
        chown -R "$SERVER_USER":shebanq "$generatedDir"
    else
        chown -R --from=$SERVER_USER "$SERVER_USER":shebanq "$generatedDir"
    fi

    echo "- Done compiling $app."
}

# make sure the group shebanq exists and the users apache and you
# are members of it

function setGroups {
    groupadd -f shebanq
    usermod -a -G shebanq apache
    usermod -a -G shebanq $SERVER_USER
}

# clone or pull shebanq into the installation directory
# i.e. ~/shebanq-install/shebanq

# make certain directories in a web2py app writable

function writableDirs {
    app=$1
    fresh=$2
    parentDir="$SERVER_APP_DIR"
    wDirs="languages log databases cache errors sessions private uploads"

    if [[ "$app" == "web2py" ]]; then
        wDirs="logs deposit"
    elif [[ "$app" == "$APP" ]]; then
        :
    else
        parentDir="$SERVER_APP_DIR/web2py/applications"
    fi
    echo "o-o-o - make writable dirs in $app"
    echo "    $wDirs"
    echo "    under $parentDir/$app"
    appPath="$parentDir/$app"
    for dir in $wDirs
    do
        dirPath="$appPath/$dir"
        if [[ ! -e "$dirPath" ]]; then
            mkdir "$dirPath"
        fi
        chmod 2775 "$dirPath"
        setfacl -d -m g::rw "$dirPath"
        if [[ "$fresh" == "v" ]]; then
            chown -R "$SERVER_USER":shebanq "$dirPath"
        else
            chown -R --from=$SERVER_USER "$SERVER_USER":shebanq "$dirPath"
        fi
    done
}

# use possibly updated parameters_443.py and routes.py and wsgihandler.py

function additionals {
    shebanqScriptDir="$SERVER_APP_DIR/$APP/scripts"
    web2pyDir="$SERVER_APP_DIR/web2py"

    for pyFile in parameters_443.py routes.py wsgihandler.py
    do
        skip="x"
        if [[ "$pyFile" == "parameters_443.py" ]]; then
            sourceFile="$SERVER_INSTALL_DIR/$pyFile"
            if [[ ! -f "$sourceFile" ]]; then
                skip="v"
                echo "Warning: administrative interface. No file $pyFile provided."
                echo "In order to use the administrative interface you need this file.
                After installation you can generate it here and put it into your
                $SERVER_INSTALL_DIR.
                Even better, copy it to you local computer in your
                _local directory in your clone of the shebanq repo.
                From there it will be picked up by subsequent runs of the provision script.
                "
            fi
        else
            sourceFile="$shebanqScriptDir/$pyFile"
        fi

        if [[ "$skip" == "x" ]]; then
            cp "$sourceFile" "$web2pyDir"
            pyPath="$web2pyDir/$pyFile"
            chown "$SERVER_USER":shebanq "$pyPath"
        fi
    done
}


# put shebanq into place
# i.e. copy it from the install location to the web-apps location

function installShebanq {
    fresh="$1"
    if [[ "$fresh" == "v" ]]; then
        label="INSTALL"
    else
        label="UPDATE"
    fi
    echo "o-o-o    $label SHEBANQ    o-o-o"

    if [[ "$fresh" == "v" ]]; then
        ensureDir "$SERVER_APP_DIR"
        chmod 755 /opt
        chmod 755 "$SERVER_APP_DIR"
    fi

    cloneDir="$SERVER_INSTALL_DIR/$APP-clone"
    shebanqDir="$SERVER_APP_DIR/$APP"
    web2pyDir="$SERVER_APP_DIR/web2py"

    # in the install procedure we wipe out an earlier shebanq at this place
    # so we remove errors, logs, uploads, etc
    # in the update procedure we preserve the existing shebanq
    if [[ "$fresh" == "v" ]]; then
        eraseDir "$shebanqDir"
    fi
    ensureDir "$shebanqDir"

    # copy the SHEBANQ repo from the install dir to the webapps dir
    # we do not copy the hidden files, such as the big .git directory
    cp -R $cloneDir/* "$shebanqDir"

    # warming up
    if [[ "$fresh" == "v" ]]; then
        chown -R "$SERVER_USER":shebanq "$shebanqDir"
    else
        chown -R --from=$SERVER_USER "$SERVER_USER":shebanq "$shebanqDir"
    fi

    if [[ -e "$web2pyDir" ]]; then
        # if some configs have changed, pick them up
        # and place them in the web2py dir
        additionals

        compileApp $APP $fresh
    fi

    # make sure the writable directories exists and have the right
    # ownership and security context
    writableDirs "$APP" "$fresh"

    ensureDir "$SERVER_CFG_DIR"
    for file in mail.cfg host.cfg mql.cfg
    do
        cp -r "$SERVER_INSTALL_DIR/$file" "$SERVER_CFG_DIR"
    done
    chown -R "$SERVER_USER":shebanq "$SERVER_CFG_DIR"
}

# run a controller of shebanq outside the apache context

function testController {
    echo "o-o-o    TEST CONTROLLER o-o-o"

    cd "$SERVER_APP_DIR/web2py"
    $TM python3 web2py.py -S $APP/hebrew/text -M > /dev/null
}

# make a first visit to SHEBANQ by means of curl

function firstVisit {
    echo "o-o-o    FIRST VISIT (this might take a minute)   o-o-o"
    echo "o-o-o An expensive index will be computed and cached"
    echo "o-o-o This may take a minute ! ..."

    protocol="https"
    flags=""
    if [[ "$firstVisitHttp"=="v" ]]; then
        protocol="http"
        flags="-L"
    elif [[ "firstVisitSloppy"=="v" ]]; then
        flags="-k"
    fi
    fullUrl="${protocol}://$SERVER_URL/$TEST_CONTROLLER"
    echo "curl $flags $fullUrl"
    $TM curl $flags "$fullUrl" | tail
    echo "o-o-o First visit done"
}
