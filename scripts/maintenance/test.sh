#!/bin/bash

# READ THIS FIRST: maintenance.md

# Script to test a server.
# Run it on the server.

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh


USAGE="
Usage: ./$(basename $0) [Options]

Test the $APP software by
- running a test controller in the web2py shell outside apache
- making a first visit using curl
- compile the shebanq app

The $APP server must be fully installed.

Options:
    --controller: only runs the test controller
    --visit: only visits the website
    --compile: just compiles the shebanq app

"

showUsage "$1" "$USAGE"

setSituation "$HOSTNAME" "Testing" "$USAGE"

doController="x"
doVisit="x"
doCompile="x"
doAll="v"

echo "o-o-o Testing ..."

if [[ "$1" == "--controller" ]]; then
    doAll="x"
    doController="v"
    shift
elif [[ "$1" == "--visit" ]]; then
    doAll="x"
    doVisit="v"
    shift
elif [[ "$1" == "--compile" ]]; then
    doAll="x"
    doCompile="v"
    shift
elif [[ "$1" == --* ]]; then
    echo "Unrecognized switch: $1"
    echo "Do ./$(basename $0) --help for available options"
    exit
fi

if [[ "$doAll" == "v" || "$doController" == "v" ]]; then
    testController
fi
if [[ "$doAll" == "v" || "$doVisit" == "v" ]]; then
    firstVisit
fi
if [[ "$doAll" == "v" || "$doCompile" == "v" ]]; then
    compileApp $APP
fi

echo "o-o-o Testing done."
