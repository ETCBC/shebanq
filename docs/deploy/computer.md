# Computer

This article describes the installation of SHEBANQ
on your computer.

**This guide is written for macos computers!**

!!! hint "Linux"
    The `macos` system offers a `unix` system under the hood,
    which is much like `linux`.
    Certain elements of the installation are the same under
    `macos`, `linux` PC, and `linux` server.

!!! caution "Windows"
    Although everything that SHEBANQ depends on also runs on Windows,
    I have never taken the trouble to put the whole process
    together in a guide, hindered as I am by not having a 
    Windos computer.
    Especially the step of compiling Emdros might be a serious
    thing to get going.

In the context of your own computer some things will be simpler than on a server.
Your computer will serve SHEBANQ in your own browser, not over the internet.

## Motivation

When developing SHEBANQ, the best way to inspect what happens behind
the screens is to have it running on your local computer.

So it is an integral part of the maintainability of SHEBANQ that
you can install it locally.

## Preparation and information

Before the actual installation of SHEBANQ, we need several software components.
We describe what they are and what you have to do first.

After that we point you to a script that completes the installation.

### Computer and operating system

You have a modern Mac, running Catalina or higher.

### Commandline tools

The key asset is the command-line, and on macos that is offered by the
`Terminal` app.
If you are not familiar with that, here is some
[reading]({{appleCmdDoc}}).

However, you will be doing deep system things, such as compiling software.
For that, you need to boost your command-line by
[tools]({{appleCmd}}) provided by Apple.

It is easy but not obvious how to get those commandline tools on your computer.
Here is a [guide]({{apleCmdInstall}}).
Even here several options are given. From all those options, choose the following:

**From a command prompt**

Open the `Terminal` app on your mac.
Give the following command:

`git`

This is an advance command, and it will trigger a prompt offering you
to download and istall the commandline tools. Do it!
It may take 5-10 minutes.

After this, you have commands to interact with GitHub, to compile software, etc.

### Homebrew

We need a package manager for macos, in order to install a mysql client later on.
Install [Homebrew]({{homebrew}}) by following the instructions on its home page and
then do

```
brew install mysql-client
```

### Python

You need Python installed, at least 3.6.3.
Preferably from [python.org]({{python}}).
After that, install the markdown module:

```
pip3 install markdown
```

### Database

We need the MySQL database system.
We are very particular about the details of installing and configuring
MySQL here.

!!! caution "No previous MySQL on your Mac"
    Preferably you do **not** have already MySQL installed.
    If you already have MySQL on your computer,
    backup your databases and remove it.
    After the install procedure for MySQL,
    you can import these backups into the new MySQL system.

There are several ways to get MySQL, but only one of them works with
[Emdros]({{emdros}}), as I found out the hard way!

You need to download the [community edition]({{mysql}}).
Take care to pick the download that matches the architecture of your mac
(`arm64` for the newer macs, `x86_64` for the usual Intel macs).
and install it in the macos way (clicking on the package in your
downloads folder and following instructions).
Do not customise anything! And leave the root password empty.
The installation process is described [here]({{mysqlInstall}}),
and it shows where you can control your databases.

### Shebanq repository

The installation script is in the Shebanq repository, so you have to
clone the repo first.
We assume you do that under a directory `github` in your home folder.
If you do not want that, you can do it somewhere else,
but then you have to tweak a setting in a configuration script later.

```
mkdir -p ~/github/etcbc
cd ~/github/etcbc
git clone https://github.com/etcbc/shebanq
cd shebanq/scripts/computer
```

Now we can do work.

## Finish MySQL configuration

In a terminal, do this (still in the same directory as above):

```
./mysql.sh
```

**Then restart the terminal.**

**Then restart the MySQL** (via its preference pane in System Preferences).

Now your database is fully functional for the purposes of SHEBANQ.

## Components

Before you run the installation script, here is some information
about what gets installed.

### Emdros

[Emdros]({{emdros}}) is the software that makes the MQL queries
possible which are so typical for SHEBANQ.
It sits in the middle of your MQL queries and the MySQL database.

The software is already packaged in the SHEBANQ repo.
The install script will take it out, unpack it, and compile it,
a lengthy process.

### Dynamic data

Dynamic data is the data that is accumulated in the database of the website
as a consequence of the actions of the users.
Think of the user accounts and the saved queries and notes.

For the local install of SHEBANQ we start fill the relevant
databases with empty data.

### Static data

Static data is the frozen data offered by the ETCBC: the text and linguistic
features of the Hebrew Bible in several versions.
That data is in the BHSA repository that we clone, and will be imported
from there, a lengthy process.

### Web2py

Our web framework is [web2py]({{web2py}}), a Python based system
to build web applications.
We install it from GitHub, and after that we plug SHEBANQ into it.
Web2Py comes with its own local webserver, so we do not have to set up 
complicated webservers such as Apache.

Instead, we can rely on the built-in webserver that comes with 
[Web2py]({{web2py}}).

## Run install script

In a terminal, do this):

```
cd ~/github/etcbc/shebanq/scripts/computer
./installmacos.sh
```

At the end, the SHEBANQ web server will be started and a first visit to the local
SHEBANQ website will be made.

## Starting and stopping SHEBANQ

You stop SHEBANQ by pressing <kbd>Ctrl</kbd> + <kbd>C</kbd> in the
terminal from where you started SHEBANQ.

You start SHEBANQ by double-clicking on the file `shebanq.command`
in your home folder, under `Applications/SHEBANQ`.

!!! hint "not the system-wide applications folder"
    Go to your home folder and find an applications folder in it.
    That is the one that contains `SHEBANQ` and there you find `shebanq.command`. 

!!! hint "shortcut"
    You can drag this file into the side bar of the Finder.
    That way you have an easy shortcut to the shebanq webapp.

## Debugging

When you browse shebanq, you might see messages in the terminal window,
and when you change the Python code in SHEBANQ and add statements that print
messages, they will show up here.

## Updating

You can update SHEBANQ by doing this in a terminal

```
cd ~/Applications/SHEBANQ
./update.sh
```

## Selective installation

You can install individual pieces.

View the options of the install script.

```
cd ~/github/etcbc/shebanq/scripts/computer
./installmacos --help
```
