#!/bin/bash

# copy data to _docker directory

# read the config settings and define functions

source ${0%/*}/configtemplate.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

dest="$DOCKER_DIR"
ensureDir "$dest"
for file in configtemplate.sh doconfig.sh functions.sh localize.sh provision.sh
do
    cp "$SCRIPT_SRC_DIR/docker/$file" "$dest"
done


if [[ ! -e "$DOCKER_DIR/config.sh" ]]; then
    echo "
Do not forget to:

cd $DOCKER_DIR
mv configtemplate.sh config.sh
vim config.sh

and adapt the contents to your situation.
"
fi
