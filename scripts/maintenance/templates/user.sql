DROP USER IF EXISTS 'shebanq'@'«DB_HOST»';
CREATE USER 'shebanq'@'«DB_HOST»' IDENTIFIED BY '«MYSQL_SHEBANQ»';
DROP USER IF EXISTS 'shebanq_admin'@'«DB_HOST»';
CREATE USER 'shebanq_admin'@'«DB_HOST»' IDENTIFIED BY '«MYSQL_SHEBANQ_ADMIN»';