# Server

This article describes the installation and maintenance of SHEBANQ
of a secure RedHat Fedora linux server.

## Acknowledgements

Thanks to
[Elia Fiore and his people]({{biblicalstudies}})
for installing SHEBANQ on RHEL/Centos/AlmaLinux/RockyLinux
and giving essential feedback.


!!! hint "Ubuntu"
    If you prefer Ubuntu, that should be easier.
    You need to change a few things: `yum` becomes `apt-get`,
    the names of installation packages might be slightly different.
    You can leave out typical selinux commands such as
    `chcon` and `setsebool`.
    Various locations maybe a little bit different.

## Tools

This repository contains a set of shell scripts
to perform installation and maintenance tasks
on SHEBANQ servers.
It also has most of the assets needed for installation.
The remaining assets are available through the
[BHSA]({{bhsa}}) repository.

!!! caution "Requirements"
    Read first to the end of this document,
    and take note of the **requirements**.

[SELINUX]({{selinux}})
might not be the most obvious choice to host SHEBANQ on,
because it is considerably more difficult to work with than Ubuntu.

However, there are a few key advantages you enjoy after the installation:

*   **prime security**

    You have SHEBANQ running on a top-notch secure system.

*   **head-ache-free software updates**

    Much of supporting software (Python, MySQL, Apache)
    can be updated without the risk of breaking things,
    because the current versions of them are supported for 
    an extra long time.
    Often, new security updates are back-ported to older versions,
    so that you can avoid upgrading to newer but incompatible versions.

The latter advantage is quite convenient for SHEBANQ, because the Emdros
software is compiled against de MySQL libraries.
So when MySQL is upgraded to a new version, Emdros has to be recompiled.
And that is something we do not want to do too often.

## Requirements

### Server

The server on which SHEBANQ is installed is a
[Security Enhanced Linux Server (SELINUX)]({{selinux}}).
You must be able to access this server by means of
[ssh]({{ssh}})
and
[scp]({{scp}}),
using a
[certificate]({{ssl}}),
so that you are not prompted for passwords.

You must have
[sudo]({{shellsudo}})
rights on this server.

If the server runs on RHEL/Centos/AlmaLinux/RockyLinux:

*   the [PowerTools repository]({{powertools}}) must be activated;
*   the Git and Development Tools packages must have been installed
*   the `mod_wsgi` module mentioned below is called `python3-mod_wsgi`.
    That means you have to modify the installation script `install.sh` before
    you run it, look for `python3-mod_wsgi` and uncomment that line,
    while commenting the line with `mod_wsgi`.


We assume that the
[Apache webserver]({{apache}})
is already installed and:

*   its config files reside in `/etc/httpd`;
*   the relevant certificates are installed in
    `/etc/pki/tls/certs` and `/etc/pki/tls/private`
*   `mod_wsgi` is not yet installed.
*   the ports 80 and 443 are open to the outside world
*   `mod_ssl` is installed and activated

!!! caution
    The installation procedure installs a bunch of Apache config file for SHEBANQ.
    It claims 1 process and 5 threads.
    You can modify this later on, manually.

    **But keep the number of processes to its default 1** (see wsgi.conf).

    Because SHEBANQ stores global data in a cache that is local
    to the process. See [Model: CACHING][models.caching.CACHING]

We assume that the following packages can be installed with `yum`.
That means that you must have the right package repositories enabled.

*   `python36`
*   `python36-devel`
*   `python3-markdown`
*   `mod_wsgi` or `python3-mod_wsgi` if on RHEL/Centos/AlmaLinux/RockyLinux
*   `mariadb`
*   `mariadb-devel`
*   `mariadb-server`

We assume that an email account is configured on the server that can be used to send
emails on behalf of SHEBANQ (for password verfication and lost passwords).

### Local computer

You have cloned the `shebanq` and `bhsa` repositories
from Github to your local computer:

```
cd ~/github/etcbc
git clone {{repoUrl}}
git clone {{bhsa}}
```

If you have cloned these long ago, you can make them up to date by
pulling them again:

```
cd ~/github/etcbc/shebanq
git pull origin master
cd ~/github/etcbc/bhsa
git pull origin master
```

You can choose to place the `github` directory somewhere else, see below,
but the structure within the `github` directory must be as prescribed.

#### The `_local` directory

The scripts in `~/github/etcbc/scripts/maintenance` have generic content.
Before working with it, the file `configtemplate` must be edited
to reflect your actual situation.
Do this as follows:

```
cd ~/github/etcbc/shebanq/scripts/maintenance
./localize.sh
```

Now you have a directory `~/github/etcbc/shebanq/_local`
And the command tells you what to do next:

*   copy `configtemplate.sh` to `config.sh`
*   edit `config.sh`

What needs to be done is:

*   adapt the `serverOther` variables to your situation:
    *   provide the name of the database host server (typically: localhost)
    *   provide passwords for mysql users named  `shebanq` and `shebanq_admin`;
        these users will be created and later in the installation process
        `shebanq_admin` is used for importing data,
        and after installation the webapp will use `shebanq`
        to fetch data in response to requests by web users.
    *   provide the locations where the https-certificates are installed
        in Apache;
        these will be used in in the httpd config file for the webapp.
    *   adapt the `mailServerOther` and `mailSenderOther` to the values
        that correspond to the email account you have configured for SHEBANQ
        emails to users.

The `_local` directory is never pushed online
(because of the `.gitignore` file in the shebanq repo),
so your local setup remains private.
Also, when you tweak files in your `_local` directory, you can still
pull new versions of the shebanq repository without overwriting your
local changes.

When you run a maintenance script, you should run them from this 
`_local` directory, to be sure that you run your
adapted version.
These local files are also the ones that are sent to the server
in the provisioning step below.

!!! hint "view and edit install.sh"
    Since installation involves running `install.sh` with root privileges,
    you are morally obliged to open `_local/install.sh` and view its contents.
    If you see something you do not understand, do not run it, or run it in
    a sandboxed (test)-machine.

    If you are on RHEL/Centos/AlmaLinux/RockyLinux, you can now make an edit in
    `_local/install.sh` and uncomment the line with `python3-mod_wsgi` in it
    and comment the line with `mod_wsgi` in it.
    

The scripts can be run from any directory, because they do not depend
on the current working directory.

## The scripts

The originals of the maintenance scripts are
in the shebanq repository
in the `scripts/maintenance` directory.
In the previous step you have copied them to the `_local`
directory.

You can run all scripts with `--help` to view the options
and arguments it accepts.

*   `backup.sh`
    *   Run it on the server.
    *   No need for root privileges.
    *   Backs up the databases that have dynamic web data:
        *   `shebanq_web`
        *   `shebanq_note`
    *   The backups are created in your home directory under `shebanq-backups`.

*   `save.sh`
    *   Run it on your local computer. It will retrieve data from the server.
    *   Saves backups of dynamic web data from the shebanq server to a
        directory on your local computer where you hold backups.
        The backup is saved in a subfolder
        `yyyy-mm-ddT-hh-mm-ss` (the datetime of the backup).

*   `provision.sh`
    *   Run it on your local computer. It will send data to the server.
    *   Copies all files needed for installation from your local
        computer to the shebanq server.
        These files end up in `shebanq-install`
        under your home directory there.
    *   The maintenance scripts themselves will be copied over
        from your `_local` directory to
        your home directory on the server.
    *   The latest backup of dynamic data from will be taken
        from your local computer and copied over to the server.
    *   You can run this script in single steps by passing an option.

*   `install.sh`
    *   Run it on the server.
    *   Run it with root privileges, e.g. `sudo ./install.sh`
    *   Installs required software
        (MySQL, Python, ModWsgi, Emdros, Web2py, and Shebanq itself)
        and loads data into the databases.

        A user group `shebanq` will be created if it does not exist;
        the user who is you and the `apache` users
        are added to the members of this group.
    *   You can run this script in single steps by passing an option.

*   `uninstall.sh`
    *   Run it on the server.
    *   Run it with root privileges, e.g. `sudo ./install.sh`
    *   Uninstalls what `install.sh` has installed.
    *   You can run this script in single steps by passing an option.

*   `restore.sh`
    *   Run it on the server.
    *   No need for root privileges.
    *   Restores the databases that have dynamic web data:
        *   `shebanq_web`
        *   `shebanq_note`
    *   They are restored from a previous backup.

*   `update.sh`
    *   Run it on the server.
    *   No need for root privileges, but you must be able to run a specific
        command with sudo without being prompted for a password:

        `sudo -n /usr/bin/systemctl restart httpd.service`

        and likewise for `start` and `stop`.
    *   Updates the shebanq webapp,
        i.e. the web-app as it is hung into the `web2py` framework.

*   `test.sh`
    *   Run it on the server.
    *   No need for root privileges.
    *   Performs a loose bunch of tasks, such as
        *   Run a controller outside Apache
        *   Visit the website
        *   Compile the application code.

## The situations

There are several situations, depending on the server that hosts SHEBANQ:

* **Production** `p`
    * url: `shebanq.ancient-data.org`
    * hosted by DANS on a KNAW server
    * publicly accessible,
    * the one and only offical shebanq website
* **Production (new)** `pn`
    * url: `server.dans.knaw.nl`
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
* **Other (new)** `on`
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

    !!! hint "url configuration"
        The shebanq configuration file that is hung into apache
        will specify a virtual host with the server name as url,
        not `shebanq.ancient-data.org`.
        In this way, the new server can be tested before changing the DNS.

1.  (new production server) `./install.sh`

    perform the complete installation of shebanq

1.  (local computer) Tweak `config.sh`

    If all went well, and shebanq works on the new machine,
    change your `_local/config.sh` and put the server name
    of the new machine in the `serverProd` variable
    (it was in the `serverProdNew` variable).

1.  (local computer) `./provision.sh p --scripts`

    upload the scripts again. Note that we use `p` now, and not `pn`.
    This has the effect that the url of the virtual host in the Apache
    config file of shebanq will be set to `shebanq.ancient-data.nl`.

1.  (new production server) `./install.sh --apache`

    This puts the updated config file in place.

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

That's all. Simple and quick.

#### A version of the static data

Do this when a new version of the etcbc data is released or an existing
version has got an update.

These databases are released through the
[etcbc/bhsa]({{bhsa}}) repository on GitHub, in the directory
[shebanq]({{bhsa}}/tree/master/shebanq).
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

1. (local computer) bulk import additional notes for the new data version

    There are currently two sets of notes that will be generated alongside
    an ETCBC data version: **crossref** and **valence**.

    Import them via the instructions mentioned
    [below](#bulk-uploading-sets-of-notes).


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


### Import massive amounts of notes

The notes facility in SHEBANQ can be used for entering personal notes,
but also for importing (big) sets of generated notes,
such as cross-references, or syntactic annotations.

Here is how to enable that function to users.

We also point to the note sets that are generated by the pipeline
alongside the BHSA and that should be imported with each ETCBC
data version.

#### Bulk uploading sets of notes

Clone the repos
[etcbc/parallels]({{parallells}}) and
[etcbc/valence]({{valence}}).

Like so:

```
cd ~/github/etcbc
git clone https://github.com/etcbc/parallels
git clone https://github.com/etcbc/valence
```

Both have a directory `shebanq` and under that subdirectories for the data versions
of the BHSA.
Go to the corresponding version, and locate the csv file that you find in each of those
places. These are the ones you will upload.

You have to be known to SHEBANQ as a *bulk uploader*.
To make somebody into a *bulk uploader*, see
[below](#make-somebody-a-bulk-uploader).

Then go to the
[notes page of shebanq]({{shebanqnotes}})
in your browser, and log in.

In the right column you see a button to upload a csv file.
Use it to upload the files we mentioned above.

The notes in those files will be imported into shebanq.

See also the [user manual]({{shebanqwikibulk}}).

#### Make somebody a bulk uploader

Users have to be added manually to the table `uploaders` in the
`shebanq_web` database. Only then they are offered to button to upload
a csv file with notes.

Find the user id in the `auth_user` table of the same database by

```
select * from auth_user where first_name = 'hey' and last_name = 'you';
```

Pick your id from the `id` column.

Then

```
insert into uploaders (uid) values (yourid);
```

That's it.

## Trouble shooting

You can add debug statements in the Python code.
We have a debug helper [M: helpers.debug][helpers.debug]

``` python
from helpers import debug

debug("here I am")
```

but you can also do simply:

```
import sys

sys.stderr.write("here I am\n")
```

If you work locally, you'll see these messages on the console.

If SHEBANQ is served under Apache, you see these messages in
the Apache log files, more precisely in

```
/var/log/httpd/shebanq_error
```

If somehow logging fails in this way and
you are desperate to get output from the server so that you can read it,
switch the `TO_RESONSE` flag on, temporarily
(it is here: [M: helpers.debug][helpers.debug]).
Then you get the messages at the top of your page, after the page has loaded.

However, use this only in emergencies or if there are discrepancies between 
the SHEBANQ on your local computer and the SHEBANQ on the server.

The recommended practice is to
[install Web2Py and SHEBANQ on your local computer](computer.md),
and debug it there.

!!! caution "SHEBANQ does not react to modified code"
    When you have modified code directly on the server, SHEBANQ does not sense it!
    Two reasons:

    Web2py uses the compiled Python code, not the Python source code.
    And due to security reasons, Apache cannot recompile the code on the fly.
    So you have to do it yourself. From your home directory on the server, run

    ``` sh
    ./test.sh --compile
    ```

    The second reason is that the whole program is in the memory of the Apache process.
    You have to restart Apache.

    ``` sh
    service httpd restart
    ```

    Mind: first compile, then restart.

    When you update shebanq from Github, by running the `update.sh` script,
    all these things are taken care of.


### SELINUX violations

If you get an internal error, but there are no Web2Py errors listed for the SHEBANQ app,
it is probably a permissions error that has nothing to do with the application logic.

Try to run the server in *permissive* mode:

```
setenforce 0
```

and make a new visit to the website.
If all is well, there you have the culprit.
Probably all stays well if you now put the mode back to enforcing:

```
setenforce 1
```

But this is not et the solution. You want to know what permission got violated.
On the server you can inspect the audit log

```
ausearch -m avc --start today
```

This gives you the violations for today. It might give you a hint to what went wrong.

Probably the webserver needed to write a file for which it had no permissions.
Obvious cases in a web2py application are:

1.  compilation of Python files. This standard Python behaviour compiles a Python
    file before running it and saves it in a `__pychache__` directory next to the
    Python scripts.
    This write action is usually not permitted in directories with code.
2.  Some directories should be writable by the webserver, such as logs, uploads, databases.
    But when these directories are removed and then recreated, their writability might
    also been gone.

To remedy this, our `install.sh` and `update.sh` take great care to
precompile all possible Python files (under `sudo`) and to
give the writable directories the right security context, whenever they are
created (`httpd_sys_rw_content_t`).

### Database permissions

The next frequent source of errors is when the database cannot be reached.
Here is a checklist:

*   The database should be up and running;
*   The required databases should be present in the database;
*   The database must allow connections with the `shebanq` user on the server;
    and, during installation, also to the `shebanq_admin` user;
*   The database should be set up with the right grants to its data;
*   The web app should provide the right credentials;
*   The web app should issue legal SQL statements.

If one of these things goes wrong, there will be error messages in the
Web2py errors for SHEBANQ.
