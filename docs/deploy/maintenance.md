# Installation and maintenance

## Motivation

**The promise of SHEBANQ to its users is that the queries and notes
they have saved on SHEBANQ will be accessible by a fixed URL
for the indefinite future.**

Therefore it is vitally important to backup this data and store
those backups in a variety of places,
not only on the server that hosts SHEBANQ,
however well that server is being managed.

The following tasks must be addressed:

*   **Server migration**

    Servers do not have eternal life,
    so every now and then SHEBANQ has to migrate
    from one server to another.

*   **'Foreign' servers**

    We encourage people to host their own SHEBANQ,
    so we must support new installations
    of SHEBANQ on third party servers.
    Those servers must be maintainable as well
    as the offical servers.

*   **Software updates**

    In order to keep SHEBANQ alive over the years,
    software updates must be carried out,
    not only of SHEBANQ itself,
    but also of the supporting systems,
    such as Emdros, Web2Py, Python, and MySQL.

* **Data updates**

    The [ETCBC](http://www.etcbc.nl), as the provider of the
    textual and linguistic data of the Hebrew Bible,
    produces occasionally data updates through its
    [BHSA](https://github.com/etcbc/bhsa) repository.
    These data updates have to find their way to the
    servers that host SHEBANQ.

In the carrying out of these tasks there are
some additional requirements which are vital for 
the long-term support of SHEBANQ.

*   **Security**

    Servers that host SHEBANQ should be secure.
    The must be hardened against attacks,
    and the user data must be kept safe,
    even if SHEBANQ only stores the bare minimum
    of personal data
    (names, email addresses, password hashes).

*   **Automation**

    Maintaining a server reuqires countless nitty-gritty
    steps, which are easily forgotten.
    That is the prime reason to automate all these steps.
    People that have not developed SHEBANQ should be able to
    maintain SHEBANQ.
    It must be straightforward to new people how to
    maintain SHEBANQ.

*   **Documentation**

    The maintenance of SHEBANQ should be well documented.
    Together with automation it is the best help we can offer
    to the maintainers if SHEBANQ in the years to come.

## Tools

This repository contains a set of shell scripts
to perform installation and maintenance tasks
on SHEBANQ servers.
It also has most of the assets needed for installation.
The remaining assets are available through the
[BHSA](https://github.com/etcbc/bhsa) repository.

!!! caution "not meant for local installations"
    Although SHEBANQ can be installed on a personal computer,
    it is not documented here.
    It is considerably easier than installing it on a server.

!!! caution "SELINUX only"
    So far, the scripts only support servers that run under
    [SELINUX](https://en.wikipedia.org/wiki/Security-Enhanced_Linux).
    Ubuntu is not currently supported.
    Again, installing SHEBANQ on Ubuntu is easier than on SELINUX.

!!! caution "Requirements"
    Read first to the end of this document,
    and take note of the **requirements**.

SELINUX might not be the most obvious choice to host SHEBANQ on,
because it is considerably more difficult to work with than Ubuntu.

However, there are a few key advantages you enjoy after the installation:

*   **prime security**

    You have SHEBANQ running on a top-notch secure system.

*   **head-ache-free software updates**

    Much of supporting software (Python, MySQL, Apache)
    can be updated without the risk of breaking things,
    because the current versions of them are supported for 
    an extra long time.
    Often, new security updates are backported to older versions,
    so that you can avoid upgrading to newer but incompatible versions.

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

### Local computer

You have cloned the `shebanq` and `bhsa` repositories
from Github to your local computer:

```
cd ~/github/etcbc
git clone https://github.com/etcbc/shebanq
git clone https://github.com/etcbc/bhsa
```

You can choose to place the `github` directory somewhere else, see below,
but the structure within the `github` directory must be as prescribed.

#### The `_local` directory

You need to create a directory `_local` in `~/github/etcbc/shebanq`
with some subdirectories, copied from the shebanq repo.

You can then make local adjustment to the configuration files.

The `_local` directory is never pushed online
(because of the `.gitignore` file in the shebanq repo),
so your local setup remains private.
Also, when you tweak files in your `_local` directory, you can still
pull new versions of the shebanq repository without overwriting your
local changes.

#### Copy files

Start with copying the maintenance scripts to the `_local` directory:

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/maintenance _local/maintenance
```

When you run a maintenance script, you should run them from your 
`_local/maintenance` directory, to be sure that you run your
adapted version.
Currently, you only have to adapt the `config.sh` script, 
the others will not get modified.
But it is very possible that your own situation is different
in ways that I have not foreseen.
In that case you can freely modify your local copies as you wish.

These local copies are also the ones that are sent to the server
in the provisioning step below.

The scripts can be run from any directory, because they do not depend
on the current working directory.

If you are going to work with your own shebanq server, do

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/cfg_other _local/cfg_other
cp -R scripts/apache_other _local/apache_other
```

If you are going to work with the offical production and test servers
of SHEBANQ, do

```
cd ~/github
cd etcbc/shebanq
cp -R scripts/cfg_other _local/cfg_prod
cp -R scripts/apache_other _local/apache_prod
cp -R scripts/cfg_other _local/cfg_test
cp -R scripts/apache_other _local/apache_test
```

#### Tweak files

You need to tweak the contents of your `_local` files to
reflect your current situation.

All maintenance scripts start with configuration.
In that way they adapt to the situation they are in.
Much of situation is described in parameters that are set in
`config.sh` which is included by all scripts.

Tweak `config.sh`:
adapt the `server`*Xxx* variables to your situation.

Tweak the files in `/apache_`*xxx*:
Adapt the url of your server, certificate locations, and other things
you might wish.

Tweak the files in `/cfg_`*xxx*:
Adapt credentials for the database connections.

## The scripts

The originals of the maintenance scripts are
in the shebanq repository
in the `scripts/maintenance` directory.
In the previous step you have copied them to the `_local`
directory.

*   `backup.sh`
    *   Run it on the server.
    *   Backup the databases that have dynamic web data:
        *   `shebanq_web`
        *   `shebanq_note`

*   `save.sh`
    *   Run it on your local computer. It will retrieve data from the server.
    *   Save backups of dynamic web data from the shebanq server to a
        directory on your local computer where you hold backups.
        The backup is saved in a subfolder
        `yyyy-mm-ddT-hh-mm-ss` (the datetime of the backup).

*   `provision.sh`
    *   Run it on your local computer. It will send data to the server.
    *   Copy all files needed for installation from your local
        computer to the shebanq server.
        These files end up in `shebanq-install`
        under your home directory there.
    *   The maintenance scripts themselves will be copied over
        from your `_local` directory to
        your home directory on the server.
    *   The latest backup of dynamic data from will be taken
        from your local computer and copied over to the server.

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

There are several situations, depending on the server that hosts SHEBANQ:

* **Production** `p`
    * url: `shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * publicly accessible,
    * the one and only offical shebanq website
* **Production (new)** `pn`
    * url: not yet `shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server,
      as a successor of the current production server
    * not yet publicly accessible,
    * not yet the one and only offical shebanq website
* **Test** `t`
    * url: `test.shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * only accessible from within the DANS-KNAW network
    * the one and only offical shebanq *test* website
* **Other** `o`
    * url: to be configured by you
    * hosted on your server
    * access managed by you
    * an unoffical shebanq website
      (very welcome, thanks for taking the trouble)
* **Other (new)** `o`
    * url: to be configured by you
    * hosted on your new server,
      as a successor to your current server
    * access managed by you
    * an unoffical shebanq website

## The scenarios

The maintenance scripts can be used in several identified scenarios,
which we spell out below.

In all situations, when on the server, you must `sudo` the invocations
of the scripts or run them as root.

It might be the case, especially on production servers,
that you do not have general sudo rights
and that the script as a whole can not be run with root privileges.
In that case you need to have rights for specific commands
to run them under sudo.
That is why in some scripts the word `sudo` still appears.
If it does not work for your situation,
you can tweak your local copy of the script.

### Install SHEBANQ on a new server 

#### Situation **Other** (first time)

This is likely your case:
you want to install SHEBANQ on a server of your choice.
For the sake of simplicity we assume that the database resides
on the server itself and we will transport and import all data needed.

We assume that this there is no previous dynamic data to be imported.

1.  (local computer) `./provision.sh o`

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

1.  (local computer) `./save.sh o`

    save backup to local computer

1.  (local computer) `./provision.sh on`

    upload all needed installation files to the server;
    the backup of the current server will be imported;
    there will also be (big) data transfers of the static databases.

1.  (new server) `./install.sh`

    perform the complete installation of shebanq

1.  Arrange with your internet provider to let the domain name point to the
    IP address of the new server

1.  (local computer) Tweak `config.sh`
    and put the name of the new server into `serverOther`.

#### **Test**

The database resides on the test server itself, data operations will be performed.

1.  (production server) `./backup.sh`

    make a backup of user data
    (only to get meaningful content in the databases)

1.  (local computer) `./save.sh p`

    save backup to local computer
    (only to get meaningful content in the databases)

1.  (local computer) `./provision.sh t`

    upload all needed installation files to the server;
    there will also be (big) data transfers of the static databases.

1.  (test server) `./install.sh`

    perform the complete installation of shebanq

#### **Production** (migrating)

The database resides on a separate database server, no data operations needed.

1.  (current production server) `./backup.sh`

    make a backup of user data
    (only for safety, if all goes well, we do not need it)

1.  (local computer) `./save.sh p`

    save backup from current production server to local computer
    (only for safety, if all goes well, we do not need it)

1.  (local computer) `./provision.sh pn`

    upload all needed installation files to the new production server;
    the static database files will be skipped.

1.  (new production server) `./install.sh`

    perform the complete installation of shebanq

1.  Arrange with your internet provider to let the domain name point to the
    IP address of the new production server

1.  (local computer) Tweak `config.sh`
    and put the name of the new production server into `serverProd`.

### Update SHEBANQ on an existing server 

This works the same in all situations.
We give the steps for the **other** situation, which is most likely your situation.

In all situations, when on the server, you must `sudo` the invocations
of the scripts or run them as root.

#### SHEBANQ code only

Do this when you noticed that the SHEBANQ repo has updates.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb

That's all. Simple and quick.

#### A version of the static data

Do this when a new version of the etcbc data is released or an existing
version has got an update.

These databases are released through the
[etcbc/bhsa](https://github.com/etcbc/bhs) repository on GitHub, in the directory
[shebanq](https://github.com/ETCBC/bhsa/tree/master/shebanq).
You have them in your local clone of the BHSA.

Below, *version* is the desired data version
that you want to import, such as
`4`, `4b`, `c`, `2017`, `2021`.

1.  (local computer) `git pull origin master`

    Do this in your clone of the BHSA repository.
    And then again in your clone of the SHEBANQ repository

1.  (local computer) `./provision.sh o --static` *version*

    upload all needed data files files to the server;

1.  (server) `install.sh --static` *version*

    This imports both the `shebanq_passage` and `shebanq_etcbc` databases of that
    version.

#### Emdros

Do this when you noticed that there is a new version of Emdros.
In that case, the SHEBANQ repository contains all that is necessary.

1.  (local computer) `git pull origin master`

    Do this in your clone of the SHEBANQ repository.

1.  (local computer) Tweak `config.sh`

    Adapt the `EMDROS_VERSION` variable so that it reflects
    the Emdros version in question.

1.  (local computer) `./provision.sh o --emdros`

    Only transfer the new Emdros distribution.

1.  (server) `./install.sh --emdros`

    Install Emdros only.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb

#### Web2py

Do this when you noticed that there is a new version of Web2py
and if you are sure that it does not break SHEBANQ.
In that case, the SHEBANQ repository contains all that is necessary.

1.  (local computer) `git pull origin master`

    Do this in your clone of the SHEBANQ repository.

1.  (local computer) `./provision.sh o --web2py`

    Only transfer the new Web2py distribution.

1.  (server) `./install.sh --web2py`

    Install Web2py only.

1.  (server) `update.sh`

    Pull the SHEBANQ repository from GitHUb

### Maintain backups of dynamic data

The dynamic data of SHEBANQ is stored in two databases:

*   `shebanq_web`:
    *   user data: names and email addresses and password hashes
        of registered users.
    *   query data: meta data and results of queries
        that have been saved in shebanq
*   `shebanq_note`:
    *   note data: metadata and content of all notes
        that have been saved in SHEBANQ.

Currently, I make occasional backups of the production SHEBANQ and store
them on my local computer, which is backed up in multiple ways,
offline and online.

#### Backup dynamic data

1. (server) `./backup.sh`

This will create a fresh backup of the dynamic data and store it
on the server in a folder with a time-stamped name.
Also, a symbolic link under the name `latest` will link to that backup.

1. (local computer) `./save.sh o`

This will fetch the latest backup from the server to your local computer.
It will end up in your backup directory there, under the same
time-stamped name, and also with a `latest` link.

#### Restore dynamic data

In cases where a server has crashed and data has been lost,
it is necessary to restore the latest known dynamic data.

1. (local computer) `./provision.sh o --dynamic`

This will find the latest dynamic data backup of the server
that exists on your local computer
and upload it to the server.

1. (server) `./restore.sh`

This will find the latest dynamic data backup that exists on the server
and import it to the databases.

!!! caution "Mixing backups"
    If you maintain multiple servers from your local computers,
    the backups of all these servers end up in the same place.

!!! hint "Production and test backups are kept separate"
    In order to avoid the risk of
    restoring a backup made on the test server to the production server,
    backups made on a test server are stored in a different directory.
    When backups are restored, they will never be taken from this directory,
    not even when restoring on the test server.

    If you do need to restore a test backup on the test server,
    you have to manually copy it over to the right place.

    The same holds for backups that come from
    the `serverOtherNew` and `serverProdNew` servers.
    These backups have no importance except for testing the processes,
    so they will be stored in the alternative place.
