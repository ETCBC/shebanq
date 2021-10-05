#!/bin/bash

source ${0%/*}/config.sh
source ${0%/*}/doconfig.sh
source ${0%/*}/functions.sh

USAGE="
Usage: ./$(basename $0)

Configures MySQL,
Adds a config file.
Creates MySQL users and gives access rights.
Restart of the MySQL system needed aftwerwards.
Use the MySQL preference pane in System Preferences for that.
"

showUsage "$1" "$USAGE"

addPath "/usr/local/opt/mysql-client/bin"
addPath "/opt/emdros/bin"
addEnv "EMDROS_HOME" "/opt/emdros"

mysqlConfDir="/usr/local/etc"
if [[ ! -e "$mysqlConfDir" ]]; then
    mkdir -p "$mysqlConfDir"
fi
cd "$mysqlConfDir"

echo "
[mysqld]
bind-address = 127.0.0.1
default-authentication-plugin=mysql_native_password
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
" > "$mysqlConfDir/my.cnf"

userSql="
DROP USER IF EXISTS 'shebanq'@'localhost';
CREATE USER 'shebanq'@'localhost' IDENTIFIED BY 'localpwd';
"

grantSql="
GRANT SELECT ON `shebanq\_etcbc%`.* TO 'shebanq'@'localhost';
GRANT SELECT ON `shebanq\_passage%`.* TO 'shebanq'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_web.* TO 'shebanq'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_note.* TO 'shebanq'@'localhost';

FLUSH PRIVILEGES;
"

echo "$userSql" | mysql -u root
echo "$grantSql" | mysql -u root
