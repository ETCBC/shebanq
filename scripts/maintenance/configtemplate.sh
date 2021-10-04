#!/bin/bash

# BEFORE YOU START !!
#
# before running any maintenance script:
#
# - read maintenance.md
# - tweak the parameters in the next section
# - read and understand the script that you want to run

# ALL_CAPS variables are used by the other scripts
# camelCase variables only occur in this file

# TWEAKING PART #################################################
#
# !!!!!!!!
# CAUTION: make sure you have copied the maintenance directory
# to the _local directory of your shebanq clone.
# This directory will not be pushed online.
#
# Do not tweak the original files in the scripts/maintenance directory
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
# Version of the Web2Py software that is in use.
# see also https://github.com/web2py/web2py
#
web2pyVersion="2.21.1-stable"
#
#
#
# Versions of the ETCBC data that you want to install/update
# NB: the shebanq software has hardcoded references to these versions.
#
STATIC_VERSIONS="4 4b 2017 c 2021"
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
BACKUP_DIR=~/Documents/shebanq/backups          # point to an existing
BACKUP_ALT_DIR=~/Documents/shebanq/backupsTest  # directory
#
#
# Where your local github directory resided, under which 
# shebanq has been cloned.
#
githubBase=~/github
#
#
# Your username on the server
#
SERVER_USER="you"  #replace by your user name on the server
#
#
# Where the Apache config files are on the server
APACHE_DIR="/etc/httpd/conf.d"
#
#
# Server specifications
# The specification of the server in the different situations
# If you work with the official SHEBANQ, the PROD and TEST servers
# are relevant.
# If you are bravely setting up SHEBANQ somewhere else,
# use the OTHER server settings.
#
# serverXxx is the server name as internet address
# 
# For each Xxx in Other, OtherNew, Test, Prod, ProdNew we define:
#
# serverUrlXxx: the url of shebanq when served from this server;
#
# dbHostXxx is the host server where the mysql database resides
#   Set it to localhost if the databases are served on a local mysql server.
#   If mysql is served on an other server,
#   we assume that the data is still in place when we install SHEBANQ.
#   So we do not create database users, administer database grants,
#   and fill database tables.
#   We also assume that the grants of the database server
#   are not host specific, so that when we access the database from a
#   new server, the same grants apply as when we used the old server
#   
serverProd="p1.dansknaw.nl"                     # deliberately wrong
serverProdNew="p2.dansknaw.nl"                  # deliberately wrong
serverUrlProd="shebanq.ancient-data.org"  # correct!
dbHostProd="m.dansknaw.nl"                      # deliberately wrong
mysqlShebanqPwdProd=xxx                         # wrong of course
mysqlShebanqAdminPwdProd=yyy                    # wrong of course
certFileProd=/etc/pki/tls/certs/ancient-data_org.cer
certKeyProd=/etc/pki/tls/private/ancient-data_org.key
certChainProd=/etc/pli/tls/certs/ancient-data_org_interm.cer

serverTest="t1.dansknaw.nl"                     # deliberately wrong
serverUrlTest="test.shebanq.ancient-data.org"
dbHostTest="localhost"
mysqlShebanqPwdTest=xxx                         # wrong of course
mysqlShebanqAdminPwdTest=yyy                    # wrong of course
certFileTest=/etc/pki/tls/certs/test_shebanq_ancient-data_org.cer
certKeyTest=/etc/pki/tls/private/test_shebanq_ancient-data_org.key
certChainTest=/etc/pli/tls/certs/test_shebanq_ancient-data_org_interm.cer

serverOther="other1.server.edu"                 # replace by your own  
serverOtherNew="other2.server.edu"              # replace by your own
serverUrlOther="shebanq.mydomain.org"           # replace by your own
dbHostOther="localhost"                         # replace by your own
mysqlShebanqPwdOther=xxx                        # obtain yourself
mysqlShebanqAdminPwdOther=yyy                   # obtain yourself
certFileOther=/etc/pki/tls/certs/other_server_edu.cer
certKeyOther=/etc/pki/tls/private/other_server_edu.key
certChainOther=/etc/pli/tls/certs/other_server_edu.cer
#
# END TWEAKING PART #################################################
