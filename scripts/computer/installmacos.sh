#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh


USAGE="
Usage: ./$(basename $0) [Options] [version]

Without options, it runs the complete installation process to
install Shebanq locally on a Mac..
By means of options, you can select exactly one step to be performed.

Options:
    --repos: fetch the shebanq and bhsa and web2py repositories from GitHub
    --emdros: the emdros software
    --dynamic: load dynamic data into mysql
    --static: load static data into mysql
    --app: hang the app together and put it in ~/Applications/SHEBANQ
    --start: run the app and visit the website

version:
    a valid SHEBANQ data version, such as 4, 4b, c, 2017, 2021
    It will restrict the static data importing to the databases
    that belong to this version.
    If left out, all versions will be done.
    Only relevant if --static is passed.

CAUTION
Take care with installing the current production server.
It might damage the current installation.
"

showUsage "$1" "$USAGE"

versions=""

if [[ "$1" == "--repos" ]]; then
    ./repos.sh
    shift
elif [[ "$1" == "--emdros" ]]; then
    ./emdros.sh
    shift
elif [[ "$1" == "--dynamic" ]]; then
    ./dynamic.sh
    shift
elif [[ "$1" == "--static" ]]; then
    shift
    if [[ "$1" != "" ]]; then
        versions="$1"
        shift
    fi
    ./static.sh "$versions"
elif [[ "$1" == "--app" ]]; then
    ./app.sh
    shift
elif [[ "$1" == "--start" ]]; then
    ./start.sh
    shift
elif [[ "$1" == --* ]]; then
    echo "Unrecognized switch: $1"
    echo "Do ./$(basename $0) --help for available options"
    exit
fi

