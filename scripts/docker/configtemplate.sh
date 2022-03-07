#!/bin/bash

# BEFORE YOU START !!
#
# before running any docker script:
#
# - read docker.md
# - tweak the parameters in the next section
# - read and understand the script that you want to run

# ALL_CAPS variables are used by the other scripts
# camelCase variables only occur in this file

# TWEAKING PART #################################################
#
# !!!!!!!!
# CAUTION: make sure you are not editing this content in its
# location scripts/maintenance/configtemplate.sh .
# Instead, create a copy _dockerconfig/config.sh and modify that.
# The directory _dockerconfig will not be pushed online.

# Do not tweak the original files in the scripts/docker directory
# !!!!!!!!
#
# Adapt the following settings to your situation before
# running the maintenance scripts.
#
#
# Version of the Emdros software that is in use.
# see also https://emdros.org
#
emdrosVersion="3.7.3"
#
#
# Version of the Web2py software that is in use.
# see also https://github.com/web2py/web2py
#
web2pyVersion="2.21.1-stable"
#
#
#
# Versions of the ETCBC data that you want to install/update
# NB: the shebanq software has hardcoded references to these versions.
#
STATIC_VERSIONS="4 4b c 2017 2021"
#
#
# Where backups of the user-generated data of shebanq can be found
# When installing the  shebanq on a new server with a
# new database, you should make a backup of this data from the current
# server with ./backup.sh which will copy it here.
# The provision script will copy that over to the server and
# import it in the new database.
# There is a separate setting for backups made on
# the test server, the new production server, and the new other server.
# So you will not inadvertently restore a non-production backup
# to the production server.
#
BACKUP_DIR=~/Documents/shebanq/backups          # point to an existing dir
#
#
# Where your local github directory resided, under which 
# shebanq has been cloned.
#
githubBase=~/github
#
#
#
# Where the Apache config files are on the server
APACHE_DIR="/etc/httpd/conf.d"
#
#
# Server specifications
#
# server is the server name as internet address
# 
# serverUrl: the url of shebanq when served from this server;
#
# dbHost is the host server where the mysql database resides
#   We assume mysql is served on an other server.
#   There is are options whether to import the static and dynamic
#   data into this database.
#   In that case we do create database users, administer database grants,
#   and fill database tables.
#   We also assume that the grants of the database server
#   are not host specific, so that when we access the database from a
#   new server, the same grants apply as when we used the old server.
#
#   We also configure mail settings: server and sender on behalf
#   of which SHEBANQ sends emails to users (for password verification)
#   Make sure that your server is set up so that it is permitted
#   to send mail for this user.
#   If you do not want the server to send mail, put an empty value
#   in the mailSender... fields.
#   
# Your username on the server
#
SERVER_USER="you"  #replace by your user name on the server
#
#
SERVER="machine.server.edu"                # replace by your own  
SERVER_URL="shebanq.mydomain.org"           # replace by your own
DB_HOST="mysql.server.edu"                  # replace by your own
MYSQL_SHEBANQ=xxx                       # obtain yourself
MYSQL_SHEBANQ_ADMIN=yyy                    # obtain yourself
CERT_FILE=/etc/pki/tls/certs/other_server_edu.cer
CERT_KEY=/etc/pki/tls/private/other_server_edu.key
CERT_CHAIN=/etc/pki/tls/certs/other_server_edu.cer
MAIL_SERVER=localhost
MAIL_SENDER=shebanq@mydomain.org
#
# END TWEAKING PART #################################################
