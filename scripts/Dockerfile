FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3.10 python3.10-dev

RUN apt-get update && \
    apt-get install -y libexpat1 apache2 apache2-utils ssl-cert libapache2-mod-wsgi-py3

RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install markdown

RUN apt-get update && \
    apt-get install -y mariadb-server libmysqlclient-dev

ARG emdrosversion="3.7.3"
ARG emdrosdir="/opt/emdros"

WORKDIR build
COPY packages/emdros-${emdrosversion}.tar.gz .

WORKDIR emdros-${emdrosversion}
RUN tar xf emdros-${emdrosversion}.tar.gz && \
    ./configure \
    --prefix=${emdrosdir} \
    --with-sqlite3=no \
    --with-mysql=yes \
    --with-swig-language-java=no \
    --with-swig-language-python2=no \
    --with-swig-language-python3=yes \
    --with-postgresql=no \
    --with-wx=no \
    --with-swig-language-csharp=no \
    --with-swig-language-php7=no \
    --with-bpt=no \
    --disable-debug && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    make && \
    make install
