REVOKE SELECT ON `shebanq\_etcbc%`.* FROM 'shebanq'@'localhost';
REVOKE SELECT ON `shebanq\_passage%`.* FROM 'shebanq'@'localhost';

REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_web.* FROM 'shebanq'@'localhost';
REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_note.* FROM 'shebanq'@'localhost';

REVOKE USAGE ON *.* FROM 'shebanq_admin'@'localhost';
REVOKE ALL PRIVILEGES ON `shebanq%`.* FROM 'shebanq_admin'@'localhost' WITH GRANT OPTION; 

FLUSH PRIVILEGES;

DROP USER shebanq@localhost;
DROP USER shebanq_admin@localhost;
