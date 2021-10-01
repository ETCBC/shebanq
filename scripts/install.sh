#!/bin/bash

# Script to install a shebanq server.
# Run it on the server.
# More info: see config.sh

source ${0%/*}/config.sh


USAGE="
Usage: ./$(basename $0) [Options]

Without options, it runs the complete installation process for a shebanq server.
By means of options, you can select exactly one step to be performed.
The server must have been provisioned.

Options:
    --python: the python programming language
    --emdros: the emdros software
    --mysqlinstall: install mariadb (drop-in replacement of mysql)
    --mysqlconfig: configure mysql
    --mysqlload: load data into mysql
    --shebanq: clone shebanq
    --web2py: install web2py
    --apache: setup apache (assume certificates are already in place)
"

showusage "$1" "$USAGE"

setscenario "$HOSTNAME" "Installing" "$USAGE"

ensuredir "$UNPACK"

doall="v"
dopython="x"
doemdros="x"
domysqlinstall="x"
domysqlconfig="x"
domysqlload="x"
doshebanq="x"
doweb2py="x"
doapache="x"

if [[ "$1" == "--python" ]]; then
    doall="x"
    dopython="v"
    shift
elif [[ "$1" == "--emdros" ]]; then
    doall="x"
    doemdros="v"
    shift
elif [[ "$1" == "--mysqlinstall" ]]; then
    doall="x"
    domysqlinstall="v"
    shift
elif [[ "$1" == "--mysqlconfig" ]]; then
    doall="x"
    domysqlconfig="v"
    shift
elif [[ "$1" == "--mysqlload" ]]; then
    doall="x"
    domysqlload="v"
    shift
elif [[ "$1" == "--shebanq" ]]; then
    doall="x"
    doshebanq="v"
    shift
elif [[ "$1" == "--web2py" ]]; then
    doall="x"
    doweb2py="v"
    shift
elif [[ "$1" == "--apache" ]]; then
    doall="x"
    doapache="v"
    shift
else
    echo "$USAGE"
    exit
fi

# Install procedure

# Python
# * install module markdown (probably sudo pip3 install markdown)

if [[ "$doall" == "v" || "$dopython" == "v" ]]; then
    echo "0-0-0    INSTALL PYTHON MODULES    0-0-0"
    yum install python36-devel
    yum install python3-markdown
fi

# MariaDB
# * install mariadb
# * configure mariadb
# * (/etc/my.cnf should contain default-character-set=utf8)
# * create users shebanq and shebanq_admin if needed
# * grant rights on tables to these users if needed

if [[ "$doall" == "v" || "$domysqlinstall" == "v" ]]; then
    echo "0-0-0    INSTALL MARIADB    0-0-0"
    yum install mariadb.x86_64
    yum install mariadb-devel.x86_64
    yum install mariadb-server.x86_64

    service mariadb start
fi

# We do Emdros right now, because some cfg files
# end up inside the emdros installation

if [[ "$doall" == "v" || "$doemdros" == "v" ]]; then
    echo "0-0-0    INSTALL EMDROS    0-0-0"
    cd "$TARGET"
    tar xvf "$EMDROS"
    cd "$EMDROSUNTAR"

    echo "EMDROS CONFIGURE"
    ./configure --prefix=$EMDROS_DIR --with-sqlite3=no --with-mysql=yes --with-swig-language-java=no --with-swig-language-python2=no --with-swig-language-python3=yes --with-postgresql=no --with-wx=no --with-swig-language-csharp=no --with-swig-language-php7=no --with-bpt=no --disable-debug

    echo "EMDROS MAKE"
    make

    echo "EMDROS INSTALL"
    make install

    cp -r "$TARGET/cfg" "$EMDROS_DIR"
    chown -R apache:apache "$EMDROS_DIR"
fi

skipusers="x"
skipgrants="x"

if [[ "$doall" == "v" || "$domysqlconfig" == "v" ]]; then
    echo "0-0-0    CONFIGURE MYSQL    0-0-0"

    if [[ "$DBHOST" == "x" ]]; then
        cp shebanq.cnf /etc/my.cnf.d/
        if [[ "$skipusers" != "v" ]]; then
            echo "0-0-0        create users        0-0-0"
            mysql -u root < "$CFG_DIR/user.sql"
        fi
        if [[ "$skipgrants" != "v" ]]; then
            echo "0-0-0        grant privileges        0-0-0"
            mysql -u root < grants.sql
        fi
    fi

    setsebool -P httpd_can_network_connect 1
    setsebool -P httpd_can_network_connect_db 1
fi

# Import data:
#   passage databases
#   emdros databases
#   user-generated-content databases

skippdb="x"
skipedb="x"
skipudb="x"

if [[ "$DBHOST" == "x" ]]; then
    if [[ "$doall" == "v" || "$domysqlload" == "v" ]]; then
        echo "0-0-0    LOAD DATA start    0-0-0"
        for version in $DATA_VERSIONS
        do
            if [[ "$skippdb" != "v" ]]; then
                echo "0-0-0        VERSION $version passage        0-0-0"
                pdbname="shebanq_passage$version"
                echo "unzipping $pdbname"
                cp "$TARGET/$pdbname.sql.gz" "$UNPACK"
                gunzip -f "$UNPACK/$pdbname.sql.gz"
                echo "loading $pdbname"
                mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt < "$UNPACK/$pdbname.sql"
                rm "$UNPACK/$pdbname.sql"
            fi

            if [[ "$skipedb" != "v" ]]; then
                echo "0-0-0        VERSION $version emdros        0-0-0"
                edbname="shebanq_etcbc$version"
                echo "unzipping $edbname"
                cp $TARGET/$edbname.mql.bz2 $UNPACK
                bunzip2 -f $UNPACK/$edbname.mql.bz2
                echo "dropping $edbname"
                mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "drop database if exists $edbname;"
                echo "importing $edbname"
                $MQL_DIR/mql -n -b m -p `cat $CFG_DIR/mqlimportopt` -u shebanq_admin -e UTF8 < $UNPACK/$edbname.mql
                rm "$UNPACK/$edbname.mql"
            fi
        done
        if [[ "$skipudb" != "v" ]]; then
            for udbname in shebanq_note shebanq_web
            do
                echo "0-0-0        DB $udbname        0-0-0"

                echo "creating fresh $udbname"
                mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "drop database if exists $udbname;"
                mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt -e "create database $udbname;"

                echo "unzipping $udbname"
                cp "$TARGET/$udbname.sql.gz" "$UNPACK"
                gunzip -f "$UNPACK/$udbname.sql.gz"

                echo "loading $udbname"
                echo "use $udbname" | cat - $UNPACK/$udbname.sql | mysql --defaults-extra-file=$CFG_DIR/mysqldumpopt

                rm "$UNPACK/$udbname.sql"
            done
        fi
        echo "0-0-0    LOAD DATA end    0-0-0"
    fi
fi

# clone shebanq

skipclone="x"

if [[ "$doall" == "v" || "$doshebanq" == "v" ]]; then
    cd "$APP_DIR"
    if [[ "$skipclone" == "v" ]]; then
        echo "0-0-0    SHEBANQ pull    0-0-0"
        cd "$SHEBANQ_DIR"
        git fetch origin
        git checkout master
        git reset --hard origin/master
        cd "$APP_DIR"
        chown -R apache:apache shebanq
        if [[ -e "$WEB2PY_DIR" ]]; then
            cd "$WEB2PY_DIR"
            python3 -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
        fi
    else
        echo "0-0-0    SHEBANQ clone    0-0-0"
        git clone "https://github.com/etcbc/shebanq"
    fi
    cp $SHEBANQ_DIR/scripts/home/*.sh $TARGETHOME
fi

# install web2py

skipwsgi="x"
skipweb2py="x"
skipshebanq="x"
skipextradirs="x"

if [[ "$doall" == "v" || "$doweb2py" == "v" ]]; then
    echo "0-0-0    WEB2PY start    0-0-0"

    if [[ "$skipwsgi" != "v" ]]; then
        echo "0-0-0        INSTALL mod_wsgi        0-0-0"
        yum install mod_wsgi
    fi

    if [[ "$skipweb2py" != "v" ]]; then
        echo "0-0-0        INSTALL web2py        0-0-0"
        ensuredir "$APP_DIR"
        chmod 755 /opt
        chmod 755 "$APP_DIR"

        cd "$APP_DIR"
        cp "$TARGET/$WEB2PY" .
        unzip $WEB2PY
        rm $WEB2PY
        mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
        cp "$TARGET/parameters_443.py" web2py
        cp "$TARGET/routes.py" web2py

        cd "$WEB2PY_DIR"
        echo "Compiling python code in admin"
        python3 -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/admin')"

        echo "Removing examples app"
        rm -rf "$WEB2PY_DIR/applications/examples"

        setsebool -P httpd_tmp_exec on
    fi

    if [[ "$skipshebanq" != "v" ]]; then
        echo "0-0-0        HOOKUP shebanq        0-0-0"
        cd "$WEB2PY_DIR/applications"
        if [[ -e shebanq ]]; then
            rm -rf shebanq
        fi
        ln -s "$APP_DIR/shebanq" shebanq

        cd "$APP_DIR"
        chown -R apache:apache web2py
        chown -R apache:apache shebanq

        if [[ -e "applications/shebanq" ]]; then
            echo "Compiling python code in shebanq"
            cd web2py
            python3 -c "import gluon.compileapp; gluon.compileapp.compile_application('applications/shebanq')"
        fi
    fi

    if [[ "$skipextradirs" != "v" ]]; then
        echo "0-0-0        MAKE writable dirs        0-0-0"
        cd "$WEB2PY_DIR/applications"
        for app in `ls`
        do
            if [[ "$app" == "__init__.py" || "$app" == "__pycache__" ]]; then
                continue
            fi
            for dir in databases cache errors sessions private uploads
            do
                if [[ -e ${app}/${dir} ]]; then
                    rm -rf ${app}/${dir}
                fi
                mkdir ${app}/${dir}
                chown apache:apache ${app}/${dir}
                chcon -R -t tmp_t ${app}/${dir}
            done
        done
    fi
fi

# configure apache

if [[ "$doall" == "v" || "$doapache" == "v" ]]; then
    echo "0-0-0    APACHE setup    0-0-0"

    if [[ -e "$APACHE_DIR/welcome.conf" ]]; then
        mv "$APACHE_DIR/welcome.conf" "$APACHE_DIR/welcome.conf.disabled"
    fi
    cp $TARGET/apache/*.conf "$APACHE_DIR"
    cp "$TARGET/wsgi.conf" "$APACHE_DIR"

    service httpd restart
fi

erasedir "$UNPACK"

# Todo after install
#
# Let DNS resolve the server name to the IP address of the newly
# installed server
