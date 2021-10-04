REVOKE SELECT ON `shebanq\_etcbc%`.* TO 'shebanq'@'localhost';
REVOKE SELECT ON `shebanq\_passage%`.* TO 'shebanq'@'localhost';

REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_web.* TO 'shebanq'@'localhost';
REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_note.* TO 'shebanq'@'localhost';

REVOKE USAGE ON *.* TO 'shebanq_admin'@'localhost';
REVOKE ALL PRIVILEGES ON `shebanq%`.* TO 'shebanq_admin'@'localhost' WITH GRANT OPTION; 

FLUSH PRIVILEGES;

DROP USER shebanq@localhost;
DROP USER shebanq_admin@localhost;
