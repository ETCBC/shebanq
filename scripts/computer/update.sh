#!/bin/bash

cd -- "$(dirname "$BASH_SOURCE")"

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Updates SHEBANQ.

Use this when the SHEBANQ code has been updated.
"

showUsage "$1" "$USAGE"

./app.sh
