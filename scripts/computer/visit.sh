#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Navigates to local SHEBANQ after 2 seconds.
"

showUsage "$1" "$USAGE"

localhost="https://127.0.0.1:8100/shebanq"

sleep 2
open "$localhost"
