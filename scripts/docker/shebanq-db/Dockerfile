FROM mysql:8

# docker run --detach --publish 3306:3306 --name shebanq-db -v ~/github/etcbc/shebanq/docker/shebanq-db/shebanq.cnf -e MYSQL_ALLOW_EMPTY_PASSWORD=1 -t shebanq-db
# docker run --detach --publish 3306:3306 --name shebanq-db -t shebanq-db -v ~/github/etcbc/shebanq/docker/shebanq-db/shebanq.cnf -e MYSQL_ROOT_PASSWORD=1

WORKDIR build
COPY user.sql grants.sql .
RUN mysql --defaults-extra-file=mysqlrootopt" < user.sql
RUN mysql --defaults-extra-file=mysqlrootopt" < grants.sql
