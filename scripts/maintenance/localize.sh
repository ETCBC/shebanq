#!/bin/bash

# copy maintenance scripts to _local directory

source ${0%/*}/configtemplate.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

ensureDir "$LOCAL_DIR"
cd "$LOCAL_DIR"

for file in backup.sh configtemplate.sh doconfig.sh functions.sh install.sh localize.sh provision.sh restore.sh save.sh uninstall.sh update.sh 'test.sh'
do
    cp "$SCRIPT_SRC_DIR/maintenance/$file" "$LOCAL_DIR"
done

if [[ ! -e "$LOCAL_DIR/config.sh" ]]; then
    echo "
Do not forget to:

cd $LOCAL_DIR
mv config.sh configold.sh
mv configtemplate.sh config.sh
vim config.sh

and adapt the contents to your situation.
"
fi
