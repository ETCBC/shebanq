#!/bin/bash

# give help if the user asks for it

function showUsage {
    if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "-?" ]]; then
        echo "$2"
        exit
    fi
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

function fetchRepo {
    org="$1"
    repo="$2"
    options="$3"
    orgDir="$githubBase/$org"
    repoDir="$orgDir/$repo"
    repoUrl="https://github.com/$org/$repo"

    if [[ -d "$repoDir" ]]; then
        echo "o-o-o    From GitHub: pull $org/$repo    o-o-o"
        cd "$repoDir"
        git pull origin master
    else
        echo "o-o-o    From GitHub: clone $org/$repo    o-o-o"
    cd "$orgDir"
        if [[ -f "$repo" ]]; then
            mv "$repo" "${repo}_saved"
        fi
        git clone $options "$repoUrl"
    fi
}

# put shebanq into place
# i.e. copy it from the install location to the web-apps location

# adds a path to to a shell startup file if it is not currently on the path

function installRepo {
    org="$1"
    repo="$2"

    echo "o-o-o    INSTALL $repo    o-o-o"

    ensureDir "$SERVER_APP_DIR"
    cd "$SERVER_APP_DIR"

    if [[ -e "$repo" ]]; then
        rm -rf "$repo"
    fi

    mkdir "$repo"
    cp -R $githubBase/$org/$repo/* "$repo"
}

function addPath {
    newPath="$1"

    if [[ ":$PATH:" == *:"$newPath":* ]]; then
       echo "already in PATH: $newPath"
    else
        statement='export PATH="'"$newPath"':$PATH''"'
        if [[ -f ~/.zprofile ]]; then
            dest=~/.zprofile
        elif [[ -f ~/.bash_profile ]]; then
            dest=~/.bash_profile
        else
            dest=~/.profile
        fi
        echo "$statement" >> "$dest"
        echo "Added statement to to include $newPath in PATH to $dest"
        $statement
    fi

}

# adds an env var to a shell start up file if it is not currently defined

function addEnv {
    newName="$1"
    newValue="$2"
    if [[ "$newName" == "$newValue" ]]; then
        echo "Already correctly defined: $newName=$newValue"
    else
        statement="export $newName="'"'"${newValue}"'"'
        if [[ -f ~/.zprofile ]]; then
            dest=~/.zprofile
        elif [[ -f ~/.bash_profile ]]; then
            dest=~/.bash_profile
        else
            dest=~/.profile
        fi
        echo "$statement" >> "$dest"
        echo "Added statement to to set $newName=$newValue to $dest"
        $statement
    fi
}

# put shebanq into place
# i.e. copy it from the install location to the web-apps location

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
