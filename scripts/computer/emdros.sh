#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Compiles and installs the Emdros software.
"

showUsage "$1" "$USAGE"

ensureDir ~/tmp
cd ~/tmp

# emdros

emdrosFile="emdros-$emdrosVersion.tar.gz"

echo "o-o-o - Emdros (may take 5-10 minutes, with alarming warnings)"

cp "$EMDROS_PATH" .
tar xvf "$EMDROS_FILE" > /dev/null
cd "$EMDROS_BARE"

./configure --prefix=/opt/emdros --with-sqlite3=local --with-mysql=yes --with-swig-language-java=no --with-swig-language-python2=no --with-swig-language-python3=yes --with-postgresql=no --with-wx=no --with-swig-language-csharp=no --with-swig-language-php7=no --with-bpt=no --disable-debug > /dev/nul

make > /dev/null

echo "o-o-o For the next step you have to enter your password"
sudo make install > /dev/null
