# Installation and maintenance

This repository contains a set of shell scripts
to perform installation and maintenance tasks
on SHEBANQ servers.
It also has most of the assets needed for installation.
The remaining assets are available through the
[BHSA](https://github.com/etcbc/bhsa) repository.


!!! caution "not meant for local installations"
    Although SHEBANQ can be installed on a personal computer,
    it is not documented here. It is considerably easier than
    installing it on a server.

!!! caution "SELINUX only"
    So far, the scripts only support servers that run under
    [SELINUX](https://en.wikipedia.org/wiki/Security-Enhanced_Linux).
    Ubuntu is not currently supported.
    Again, installing SHEBANQ on Ubuntu is easier than on SELINUX.

!!! caution "Requirements"
    Read first to the end of this document, and take note of the **requirements**.

## Requirements

### Server

The server on which SHEBANQ is installed is a
[Security Enhanced Linux Server (SELINUX)](https://en.wikipedia.org/wiki/Security-Enhanced_Linux).
You must be able to access this server by means of
[ssh](https://man.openbsd.org/ssh.1)
and
[scp](https://man.openbsd.org/scp.1),
using a
[certificate](https://smallstep.com/blog/use-ssh-certificates/),
so that you are not prompted for passwords.

You must have
[sudo](https://linuxtect.com/linux-sudo-command-run-commands-with-root-privileges/)
rights on this server.

We assume that the
[Apache webserver](https://httpd.apache.org)
is already installed and:

*   its config files reside in `/etc/httpd`;
*   the relevant certificates are installed in
    `/etc/pki/tls/certs` and `/etc/pki/tls/private`
*   `mod_wsgi` is not yet installed.

### Local machine
You have cloned the `shebanq` and `bhsa` repositories
from Github to your local computer:

```
cd ~/github/etcbc
git clone https://github.com/etcbc/shebanq
git clone https://github.com/etcbc/bhsa
```

You can choose to place the `github` directory somewhere else, see below,
but the structure within the `github` directory must be as prescribed.

You need to create a directory `_local` in `~/github/etcbc/shebanq`
with some subdirectories, copied from the shebanq repo.

This directory is never pushed online
(because of the `.gitignore` file in this repo),
so your local setup remains private.
Also, when you tweak files in your `_local` directory, you can still
pull new versions of the shebanq repository without overwriting your
local changes.


Start with copying the maintenance scripts to the `_local` directory:

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/maintenance _local/maintenance
```

When you run a maintenance script, do run your local copy.
These are also the copies that are sent to the server in the provisioning step
below.

If you are going to work with your own shebanq server, do

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/cfg_other _local/cfg_other
cp -R scripts/apache_other _local/apache_other
```

If you are going to work with the offical shebanq and its production and test servers,
do

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/cfg_other _local/cfg_prod
cp -R scripts/apache_other _local/apache_prod
cp -R scripts/cfg_other _local/cfg_test
cp -R scripts/apache_other _local/apache_test
```

You need to tweak the contents of your `_local` files to
reflect your current situation.

All maintenance scripts start with configuration.
In that way they adapt to the situation they are in.
Much of situation is described in parameters that are set in
`config.sh` which is included by all scripts.

Tweak `config.sh`:
adapt the `MACHINE` variables to your situation.

Tweak the files in `/apache_`*xxx*:
Adapt the url of your server, certificate locations, and other things
you might wish.

Tweak the files in `/cfg_`*xxx*:
Adapt credentials for the database connections.

## The scripts

You find them in the shebanq repository in the `scripts` directory.

*   `backup.sh`
    *   Run it on the server.
    *   Backup the databases that have dynamic web data:
        *   `shebanq_web`
        *   `shebanq_note`

*   `save.sh`
    *   Run it on your local machine.
    *   Save backups of dynamic web data from the shebanq server to a
        directory on your local machine where you hold backups.
        The backup is saved in a subfolder
        `yyyy-mm-ddT-hh-mm-ss` (the datetime of the backup).

*   `provision.sh`
    *   Run it on your local machine.
    *   Copy all files needed for installation from your local
        machine to the shebanq server.
        These files end up in `shebanq-install` under your home directory there.
    *   The maintenance scripts themselves will be copied over
        to your home directory on the server.
    *   The latest backup of dynamic data from will be taken from your
        local computer and copied over to the server.

*   `install.sh`
    *   Run it on the server.
        Install and configure required software.
        MySQL, Python, Emdros, Web2py, shebanq itself.
    *   Install `mod_wsgi` and configure the apache webserver.
    *   Fill the databases with data, if needed.

*   `restore.sh`
    *   Run it on the server.
    *   Restore the databases that have dynamic web data:
        *   `shebanq_web`
        *   `shebanq_note`
    *   They are restored from a previous backup.

*   `update.sh`
    *   Run it on the server.
    *   Update the shebanq software, i.e. the web-app as it is hung into
        the `web2py` framework.


## The situations

There are three situations, depending on the server that hosts SHEBANQ:

* **Production**
    * url: `shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * publicly accessible,
    * the one and only offical shebanq website
* **Production (new)**
    * url: not yet `shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * not yet publicly accessible,
    * not yet the one and only offical shebanq website
* **Test**
    * url: `test.shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * only accessible from within the DANS-KNAW network
    * the one and only offical shebanq *test* website
* **Other**
    * url: to be configured by you
    * hosted on your server
    * access managed by you
    * an unoffical shebanq website (very welcome, thanks for taking the trouble)

## The scenarios

The maintenance scripts can be used as follows in several identified scenarios:

### Install SHEBANQ on a new server 

In all situations, when on the server, you must `sudo` the invocations
of the scripts or run them as root.

#### Situation **Other** (first time)

This is likely your case: you want to install SHEBANQ on a server
of your choice.
For the sake of simplicity we assume that the database resides
on the server itself and we will transport and import all data needed.

We assume that this there is no previous dynamic data to be imported.

1.  (local machine) `./provision.sh o`

    upload all needed installation files to the server;
    there will also be (big) data transfers of the static databases.

1.  (server) `./install.sh`

    perform the complete installation of shebanq

1.  Arrange with your internet provider to let the domain name point to the
    IP address of the server

#### **Other** (migrating)

You have a server with SHEBANQ running and want to migrate to a new server.

1.  (current server) `./backup.sh`

    make a backup of user data

1.  (local machine) `./save.sh o`

    save backup to local machine

1.  (local machine) `./provision.sh on`

    upload all needed installation files to the server;
    the backup of the old machine will be imported;
    there will also be (big) data transfers of the static databases.

1.  (new server) `./install.sh`

    perform the complete installation of shebanq

1.  Arrange with your internet provider to let the domain name point to the
    IP address of the new server

#### **Test**

The database resides on the test server itself, data operations will be performed.

1.  (production server) `./backup.sh`

    make a backup of user data
    (only to get meaningful content in the databases)

1.  (local machine) `./save.sh p`

    save backup to local machine
    (only to get meaningful content in the databases)

1.  (local machine) `./provision.sh t`

    upload all needed installation files to the server;
    there will also be (big) data transfers of the static databases.

1.  (test server) `./install.sh`

    perform the complete installation of shebanq

#### **Production** (migrating)

The database resides on a separate database server, no data operations needed.

1.  (current production server) `./backup.sh`

    make a backup of user data
    (only for safety, if all goes well, we do not need it)

1.  (local machine) `./save.sh p`

    save backup from current production server to local machine
    (only for safety, if all goes well, we do not need it)

1.  (local machine) `./provision.sh pn`

    upload all needed installation files to the new production server;
    the static database files will be skipped.

1.  (new production server) `./install.sh`

    perform the complete installation of shebanq

1.  Arrange with your internet provider to let the domain name point to the
    IP address of the new production server

### Update SHEBANQ on an existing server 

This works the same in all situations.
We give the steps for the **other** situation, which is most likely your situation.

In all situations, when on the server, you must `sudo` the invocations
of the scripts or run them as root.

#### SHEBANQ code only

Do this when you noticed that the SHEBANQ repo has updates.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb

#### A version of the static data

Do this when a new version of the etcbc data is released or an existing
version has got an update.

These databases are released through the
[etcbc/bhsa](https://github.com/etcbc/bhs) repository on GitHub, in the directory
[shebanq](https://github.com/ETCBC/bhsa/tree/master/shebanq).
You can download these files individually.

1.  (local machine) `git pull origin master`

    Do this in your clone of the BHSA repository.
    And then again in your clone of the SHEBANQ repository

1.  (local machine) Tweak `config.sh`

    Adapt the `DATA_VERSIONS` variables so that it only contains
    the version in question.

1.  (local machine) `./provision.sh o --static`

    upload all needed data files files to the server;

1.  (server) `update.sh -d` *version*

    where version is the desired data version that you want to import,
    such as `4`, `4b`, `2017`, `2021`.

    This imports both the `shebanq_passage` and `shebanq_etcbc` databases of that
    version.
    If you pass `-de` instead of `-d`, only the `shebang_etcbc` database
    will be imported. 

#### Emdros

Do this when you noticed that there is a new version of Emdros.
In that case, the SHEBANQ repository contains all that is necessary.

1.  (local machine) `git pull origin master`

    Do this in your clone of the SHEBANQ repository.

1.  (local machine) Tweak `config.sh`

    Adapt the `EMDROS_VERSION` variable so that it reflects
    the Emdros version in question.

1.  (local machine) `./provision.sh o --emdros`

    Only transfer the new Emdros distribution.

1.  (server) `./install.sh --emdros`

    Install Emdros only.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb

#### Web2py

Do this when you noticed that there is a new version of Web2py
and if you are sure that it does not break SHEBANQ.
In that case, the SHEBANQ repository contains all that is necessary.

1.  (local machine) `git pull origin master`

    Do this in your clone of the SHEBANQ repository.

1.  (local machine) `./provision.sh o --web2py`

    Only transfer the new Web2py distribution.

1.  (server) `./install.sh --web2py`

    Install Web2py only.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb
